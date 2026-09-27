"""
config.py
---------
Loads secrets (API keys) from environment variables / a local .env file
(for local development) or Streamlit Cloud's secrets manager (for
deployment) — NEVER hardcode an API key directly in source code. Source
files get committed to Git and pushed to GitHub; a hardcoded key in a
public repo gets found and abused within minutes by automated scanners.

Setup (one-time, on your own machine):
  1. Copy .env.example to a new file named exactly .env
  2. Open .env and paste your real Gemini API key after the = sign
  3. .env is listed in .gitignore, so it will never be committed to GitHub

On Streamlit Community Cloud, set the same key/value under
"Manage app" -> Settings -> Secrets instead — there is no .env file there.

If GEMINI_API_KEY is not set, GEMINI_ENABLED will be False and the app
will gracefully fall back to the classic OpenCV + Tesseract pipeline
instead of crashing.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file, if present


def _get_secret(key: str, default: str = "") -> str:
    """Check env vars first (local dev), then Streamlit Cloud secrets."""
    value = os.environ.get(key, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(key, default)).strip()
    except Exception:
        return default


GEMINI_API_KEY = _get_secret("GEMINI_API_KEY")
GEMINI_ENABLED = bool(GEMINI_API_KEY)
GEMINI_MODEL = _get_secret("GEMINI_MODEL", "gemini-3.1-flash-lite")