"""
config.py
---------
Loads secrets (API keys) from environment variables / a local .env file —
NEVER hardcode an API key directly in source code. Source files get
committed to Git and pushed to GitHub; a hardcoded key in a public repo
gets found and abused within minutes by automated scanners.

Setup (one-time, on your own machine):
  1. Copy .env.example to a new file named exactly .env
  2. Open .env and paste your real Gemini API key after the = sign
  3. .env is listed in .gitignore, so it will never be committed to GitHub

If GEMINI_API_KEY is not set, GEMINI_ENABLED will be False and the app
will gracefully fall back to the classic OpenCV + Tesseract pipeline
instead of crashing.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file, if present

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_ENABLED = bool(GEMINI_API_KEY)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
