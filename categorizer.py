"""
categorizer.py
--------------
Expense categorization from Gemini AI detection, with keyword-based fallback.
"""

from typing import List, Optional

CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "cafe", "coffee", "restaurant", "kitchen", "diner", "pizza", "burger",
        "bakery", "food", "eatery", "dhaba", "biryani", "tea", "juice", "canteen",
    ],
    "Groceries": [
        "mart", "supermarket", "grocery", "bazaar", "provision", "kirana",
        "fresh", "store",
    ],
    "Travel & Transport": [
        "uber", "ola", "taxi", "cab", "fuel", "petrol", "diesel", "metro",
        "railway", "airlines", "airways", "parking",
    ],
    "Utilities": [
        "electricity", "water board", "gas", "broadband", "internet", "recharge",
        "mobile bill", "dth",
    ],
    "Shopping": [
        "mall", "fashion", "apparel", "electronics", "retail", "outlet",
    ],
    "Health": [
        "pharmacy", "clinic", "hospital", "medical", "chemist", "diagnostics",
    ],
    "Entertainment": [
        "cinema", "movie", "multiplex", "theatre", "gaming",
    ],
}

ALL_CATEGORIES = list(CATEGORY_KEYWORDS.keys()) + ["Other"]

__all__ = ["categorize", "ALL_CATEGORIES", "CATEGORY_KEYWORDS"]


def categorize(
    vendor: str = "",
    item_names: Optional[List[str]] = None,
    ai_category: Optional[str] = None,
) -> str:
    """
    Determine the category of an expense.
    1. If Gemini AI detected a valid category, map and return that.
    2. Otherwise, fall back to keyword heuristics on vendor and item names.
    3. Default to 'Other' if no match.
    """
    if ai_category:
        clean_ai = ai_category.strip().lower()
        for cat in ALL_CATEGORIES:
            if cat.lower() == clean_ai:
                return cat
        for cat in ALL_CATEGORIES:
            if cat.lower() in clean_ai or clean_ai in cat.lower():
                return cat

    text = (vendor or "").lower()
    if item_names:
        text += " " + " ".join(item_names).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "Other"

