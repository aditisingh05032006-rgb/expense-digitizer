"""
ledger.py
---------
A simple persistent expense ledger backed by a CSV file. Kept deliberately
separate from the Streamlit app so the ledger logic is testable and
reusable outside the UI (e.g. from a CLI script or a notebook).
"""

import os
import json
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LEDGER_PATH = os.path.join(DATA_DIR, "expenses_ledger.csv")
BUDGET_PATH = os.path.join(DATA_DIR, "budgets.csv")
COLUMNS = ["timestamp", "date", "vendor", "category", "total", "items", "ocr_confidence"]


# ------------------------------------------------------------------ Ledger
def load_ledger() -> pd.DataFrame:
    if os.path.exists(LEDGER_PATH):
        return pd.read_csv(LEDGER_PATH)
    return pd.DataFrame(columns=COLUMNS)


def is_duplicate(vendor: str, date: str, total: float, df: pd.DataFrame = None) -> bool:
    """Flags a likely duplicate: same vendor, same date, same total already
    logged. Doesn't block saving — just lets the UI warn before committing."""
    if df is None:
        df = load_ledger()
    if df.empty:
        return False
    match = (
        (df["vendor"].astype(str).str.strip().str.lower() == str(vendor).strip().lower())
        & (df["date"].astype(str).str.strip() == str(date).strip())
        & (df["total"].astype(float).round(2) == round(float(total or 0), 2))
    )
    return bool(match.any())


def append_expense(vendor: str, date: str, category: str, total: float,
                    items: list, ocr_confidence: float) -> pd.DataFrame:
    df = load_ledger()
    new_row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "date": date or "",
        "vendor": vendor or "Unknown",
        "category": category,
        "total": total or 0.0,
        "items": json.dumps(items),
        "ocr_confidence": ocr_confidence,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(LEDGER_PATH, index=False)
    return df


def delete_expense(row_index: int) -> pd.DataFrame:
    """Deletes a single row by its DataFrame index and re-saves the ledger."""
    df = load_ledger()
    df = df.drop(index=row_index).reset_index(drop=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(LEDGER_PATH, index=False)
    return df


def update_expense(row_index: int, **fields) -> pd.DataFrame:
    """Edits one or more fields (vendor, date, category, total) on an
    existing row, identified by its DataFrame index."""
    df = load_ledger()
    for key, value in fields.items():
        if key in df.columns:
            df.loc[row_index, key] = value
    df.to_csv(LEDGER_PATH, index=False)
    return df


def overwrite_ledger(edited_df: pd.DataFrame) -> pd.DataFrame:
    """Replaces the whole ledger with an edited DataFrame — used by the
    interactive data-editor table, where the user can edit or mark several
    rows at once before saving all changes in one action."""
    os.makedirs(DATA_DIR, exist_ok=True)
    edited_df = edited_df[COLUMNS].copy()
    edited_df.to_csv(LEDGER_PATH, index=False)
    return edited_df


def spend_by_category(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    return df.groupby("category")["total"].sum().sort_values(ascending=False)


def spend_over_time(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    parsed_dates = pd.to_datetime(df["timestamp"])
    return df.groupby(parsed_dates.dt.date)["total"].sum()


# ------------------------------------------------------------------ Budgets
def load_budgets() -> dict:
    """Returns {category: monthly_budget_amount}."""
    if os.path.exists(BUDGET_PATH):
        budget_df = pd.read_csv(BUDGET_PATH)
        return dict(zip(budget_df["category"], budget_df["monthly_budget"]))
    return {}


def save_budget(category: str, amount: float) -> dict:
    budgets = load_budgets()
    budgets[category] = amount
    budget_df = pd.DataFrame(
        [{"category": c, "monthly_budget": a} for c, a in budgets.items()]
    )
    os.makedirs(DATA_DIR, exist_ok=True)
    budget_df.to_csv(BUDGET_PATH, index=False)
    return budgets


def current_month_spend_by_category(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    parsed = pd.to_datetime(df["timestamp"])
    this_month = df[
        (parsed.dt.month == datetime.now().month) & (parsed.dt.year == datetime.now().year)
    ]
    if this_month.empty:
        return pd.Series(dtype=float)
    return this_month.groupby("category")["total"].sum()
