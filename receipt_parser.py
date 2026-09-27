"""
receipt_parser.py
------------------
Turns raw OCR text from a receipt into structured fields: vendor, date,
line items, and total.

Receipts don't have consistent structure across vendors (unlike a form),
so this uses heuristics rather than a single fixed regex — same
philosophy as the field_extractor in the earlier document project, but
adapted to receipt-specific patterns:
  - Vendor: usually the first substantial text line (store name/logo text)
  - Date: regex over common date formats
  - Total: the line containing "total" (but NOT "subtotal") with a
    trailing amount; falls back to the largest currency amount found
  - Line items: lines that end in a price-like number
"""

import re
from dataclasses import dataclass, field
from typing import Optional

DATE_RE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
# Matches amounts like 1,234.56 / 45.00 / ₹120 / $9.99
AMOUNT_RE = re.compile(r"[₹$€]?\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?")
TOTAL_LINE_RE = re.compile(r"(?<!sub)total", re.IGNORECASE)
NON_ITEM_LINE_RE = re.compile(r"\b(sub\s?total|total|tax|gst|vat|cgst|sgst|discount|change|tendered|cash|card)\b", re.IGNORECASE)
ITEM_LINE_RE = re.compile(r"^(.{2,40}?)\s{1,}([₹$€]?\s?\d{1,4}(?:\.\d{1,2})?)\s*$")


@dataclass
class LineItem:
    name: str
    price: float


@dataclass
class ParsedReceipt:
    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    items: list = field(default_factory=list)
    raw_text: str = ""


def _clean_amount(raw: str) -> Optional[float]:
    cleaned = re.sub(r"[₹$€,\s]", "", raw)
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def extract_vendor(lines: list) -> Optional[str]:
    for line in lines[:5]:
        stripped = line.strip()
        # Skip lines that are mostly numbers/symbols (unlikely to be a store name)
        letters = sum(c.isalpha() for c in stripped)
        if len(stripped) >= 3 and letters >= max(3, len(stripped) * 0.5):
            return stripped
    return None


def extract_date(text: str) -> Optional[str]:
    match = DATE_RE.search(text)
    return match.group(0) if match else None


def extract_total(lines: list) -> Optional[float]:
    candidates = []
    for line in lines:
        if TOTAL_LINE_RE.search(line):
            amounts = AMOUNT_RE.findall(line)
            for a in amounts:
                val = _clean_amount(a)
                if val is not None:
                    candidates.append(val)
    if candidates:
        return max(candidates)  # "Total" lines sometimes also contain a tendered/change amount

    # Fallback: largest currency-like amount anywhere in the receipt
    all_amounts = [_clean_amount(a) for a in AMOUNT_RE.findall("\n".join(lines))]
    all_amounts = [a for a in all_amounts if a is not None]
    return max(all_amounts) if all_amounts else None


def extract_items(lines: list) -> list:
    items = []
    for line in lines:
        if NON_ITEM_LINE_RE.search(line):
            continue
        match = ITEM_LINE_RE.match(line.strip())
        if match:
            name, price_raw = match.groups()
            price = _clean_amount(price_raw)
            if price is not None and len(name.strip()) >= 2:
                items.append(LineItem(name=name.strip(), price=price))
    return items


def parse_receipt(text: str) -> ParsedReceipt:
    lines = [l for l in text.split("\n") if l.strip()]
    return ParsedReceipt(
        vendor=extract_vendor(lines),
        date=extract_date(text),
        total=extract_total(lines),
        items=extract_items(lines),
        raw_text=text,
    )
