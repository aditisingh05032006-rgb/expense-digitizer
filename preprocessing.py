"""
preprocessing.py
-----------------
OpenCV preprocessing tuned for receipts specifically: receipts are long,
narrow, low-contrast thermal-printer prints (often faded or slightly
crumpled), which behave differently under OCR than a flat business card
or document. This pipeline adds contrast enhancement (CLAHE) on top of
the denoise/threshold/deskew pipeline for that reason.
"""

import cv2
import numpy as np


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image at {path}")
    return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    """CLAHE (adaptive histogram equalization) — helps a lot on faded
    thermal-printer receipts where ink has partially worn off."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def denoise(gray: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoising(gray, h=10)


def adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=25,
        C=12,
    )


def deskew(img: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(img < 255))
    if coords.size == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.5:
        return img
    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def preprocess(path: str) -> np.ndarray:
    img = load_image(path)
    gray = to_grayscale(img)
    contrasted = enhance_contrast(gray)
    denoised = denoise(contrasted)
    thresh = adaptive_threshold(denoised)
    straightened = deskew(thresh)
    return straightened
