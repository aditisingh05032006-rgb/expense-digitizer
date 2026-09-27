"""
ocr_engine.py
-------------
Tesseract OCR wrapper with per-word confidence, tuned for the sparse,
column-like text layout of receipts (psm 6 = uniform block of text,
which works well for the line-by-line item lists on most receipts).
"""

import os
import platform
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import numpy as np
from dataclasses import dataclass

# On Windows, Tesseract often isn't added to PATH automatically even when
# installed, which makes pytesseract fail with a confusing error. This
# checks the default install location as a fallback so beginners don't
# have to manually edit PATH environment variables.
if platform.system() == "Windows":
    _default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_default_win_path):
        pytesseract.pytesseract.tesseract_cmd = _default_win_path


@dataclass
class OcrResult:
    text: str
    mean_confidence: float


def run_ocr(image: np.ndarray, config: str = "--psm 6") -> OcrResult:
    text = pytesseract.image_to_string(image, config=config)
    data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
    confidences = [int(c) for c in data["conf"] if c != "-1"]
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return OcrResult(text=text.strip(), mean_confidence=round(mean_conf, 1))
