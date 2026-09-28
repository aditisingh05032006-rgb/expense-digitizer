"""
gemini_extractor.py
--------------------
AI-powered extraction using Google's Gemini API.

Reliability features:
  - Auto-retry with exponential backoff on 503 / 429 (overload) errors
  - Fallback model chain: primary → gemini-2.0-flash → gemini-1.5-flash
  - Image compressed before upload for faster transfer
  - Client singleton — created once, reused on every scan
"""

import io
import time
import logging
from typing import List

from PIL import Image
from pydantic import BaseModel
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_ENABLED

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model priority list — tries each in order if the previous one is unavailable
# ---------------------------------------------------------------------------
_MODEL_CHAIN = [
    "gemini-2.0-flash",        # fastest current stable model
    "gemini-2.0-flash-lite",   # even lighter / cheaper
    "gemini-1.5-flash",        # proven fallback
    "gemini-1.5-flash-8b",     # smallest fallback
]

# Retry settings for 503 / 429 overload errors
_MAX_RETRIES = 3
_RETRY_DELAY = 1.5  # seconds (doubles each attempt)


class GeminiExtractionError(Exception):
    pass


# ---------------------------------------------------------------------------
# Singleton client
# ---------------------------------------------------------------------------
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None and GEMINI_ENABLED:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# Image compression — shrinks payload from ~3-5 MB → ~150 KB
# ---------------------------------------------------------------------------
def _compress_image(image: Image.Image, max_px: int = 1024, quality: int = 85) -> Image.Image:
    img = image.copy()
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    return Image.open(buf)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ReceiptItemSchema(BaseModel):
    name: str
    price: float


class ReceiptSchema(BaseModel):
    vendor: str
    date: str
    total: float
    category: str = "Other"
    items: List[ReceiptItemSchema]


PROMPT = """You are reading a photo of a purchase receipt, which may be
crumpled, photographed at an angle, or partly obscured by a hand or shadow.

Extract:
- vendor: the store/business name
- date: the date shown on the receipt, in the same format it appears (e.g. DD/MM/YYYY or YYYY-MM-DD)
- total: the final total amount actually paid (not the subtotal)
- category: automatically categorize this receipt into the single best match among:
  * "Food & Dining" (restaurants, cafes, fast food, bakeries, food delivery, bars)
  * "Groceries" (supermarkets, grocery stores, provisions, marts, daily essentials)
  * "Travel & Transport" (fuel, petrol, diesel, taxi, cab, uber, ola, metro, train, flight, parking)
  * "Utilities" (electricity, water, gas, internet/broadband, mobile recharge, utility bills)
  * "Shopping" (clothing, electronics, retail stores, accessories, merchandise)
  * "Health" (pharmacy, medicines, clinics, hospital, diagnostic tests)
  * "Entertainment" (movies, cinema, gaming, amusement, subscriptions, events)
  * "Other" (any other miscellaneous expense)
- items: every purchased line item with its name and price

If a field truly cannot be determined even by inferring from context,
use an empty string for text fields, "Other" for category, or 0 for numbers.
"""


# ---------------------------------------------------------------------------
# Core extraction with retry + model fallback
# ---------------------------------------------------------------------------
def _try_model(client: genai.Client, model: str, image: Image.Image) -> ReceiptSchema:
    """Attempt extraction with one specific model, retrying on transient errors."""
    delay = _RETRY_DELAY
    last_err: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[PROMPT, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ReceiptSchema,
                ),
            )
            return ReceiptSchema.model_validate_json(response.text)

        except Exception as e:
            err_str = str(e)
            is_transient = any(code in err_str for code in ("503", "429", "UNAVAILABLE", "Resource has been exhausted"))

            if is_transient and attempt < _MAX_RETRIES:
                logger.warning("Model %s attempt %d/%d failed (transient): %s. Retrying in %.1fs…",
                               model, attempt, _MAX_RETRIES, err_str[:80], delay)
                time.sleep(delay)
                delay *= 2  # exponential backoff
                last_err = e
            else:
                raise  # non-transient or last attempt — propagate

    raise last_err  # shouldn't reach here, but satisfies type checker


def extract_with_gemini(image_path: str) -> ReceiptSchema:
    if not GEMINI_ENABLED:
        raise GeminiExtractionError(
            "No Gemini API key configured. Add GEMINI_API_KEY to your .env file."
        )

    client = _get_client()
    image = _compress_image(Image.open(image_path))

    last_error: Exception | None = None
    for model in _MODEL_CHAIN:
        try:
            result = _try_model(client, model, image)
            logger.info("Extracted with model: %s", model)
            return result
        except Exception as e:
            logger.warning("Model %s failed: %s — trying next model…", model, str(e)[:100])
            last_error = e
            continue

    raise GeminiExtractionError(
        f"All models unavailable. Last error: {last_error}"
    ) from last_error
