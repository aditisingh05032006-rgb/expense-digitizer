"""
gemini_extractor.py
--------------------
An alternative, AI-powered extraction path using Google's Gemini API,
sitting alongside (not replacing) the classic OpenCV + Tesseract + regex
pipeline in preprocessing.py / ocr_engine.py / receipt_parser.py.

Why keep both instead of switching entirely?
  - The classic pipeline is free, works offline, and needs no API key —
    good for judging your own OCR/CV skills in an interview.
  - Gemini reads the image directly with a vision-language model, so it
    handles messy real-world photos (crumpled paper, an angle, a thumb
    partly covering text) far more robustly than OCR-then-regex, since
    it understands context instead of just recognizing characters.
  - Having BOTH and being able to explain the trade-off (cost/network
    dependency vs. accuracy on hard images) is a stronger portfolio
    story than only having one.

This module fails gracefully: if no API key is configured, or the API
call errors out, it raises GeminiExtractionError with a clear message —
the calling code (app.py) is expected to catch this and fall back to the
classic pipeline.
"""

from typing import List
from PIL import Image
from pydantic import BaseModel
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_ENABLED


class GeminiExtractionError(Exception):
    pass


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
use an empty string for text fields, "Other" for category, or 0 for numbers. Do not guess wildly —
only fill in what's reasonably supported by what's visible in the image.
"""


def extract_with_gemini(image_path: str) -> ReceiptSchema:
    if not GEMINI_ENABLED:
        raise GeminiExtractionError(
            "No Gemini API key configured. Add GEMINI_API_KEY to your .env file."
        )

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        image = Image.open(image_path)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[PROMPT, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReceiptSchema,
            ),
        )
        return ReceiptSchema.model_validate_json(response.text)

    except Exception as e:
        # Wrap every failure mode (bad key, network issue, quota exceeded,
        # malformed response) into one clear error type the UI can catch.
        raise GeminiExtractionError(f"Gemini extraction failed: {e}") from e
