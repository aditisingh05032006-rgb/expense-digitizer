# Expense & Receipt Digitizer

Photograph a receipt → get back vendor, date, itemized costs, and total,
auto-categorized (Food, Travel, Groceries, etc.) and logged to a running
expense ledger you can browse in a dashboard.

This is a simplified version of the OCR pipeline that powers apps like
Expensify, Splitwise's receipt scan, and corporate expense-reporting tools.

## Why this project

Unlike a generic "OCR demo," this one makes a judgment call at every step
and is upfront about the trade-off, which is exactly what gets asked about
in interviews:

- **Preprocessing is receipt-specific, not generic.** Thermal-printer
  receipts are faded and low-contrast in a way flat documents aren't, so
  this pipeline adds CLAHE contrast enhancement on top of the standard
  denoise/threshold/deskew steps (see `preprocessing.py`).
- **Parsing is heuristic, not a fixed template.** Receipts have no
  consistent layout across vendors, so `receipt_parser.py` uses rules
  (first substantial line = vendor, "total" line but not "subtotal" =
  total, price-suffixed lines = items) instead of one rigid regex —
  and explains in comments why each rule exists.
- **Categorization is rule-based on purpose, not by accident.** With no
  labeled training data yet, `categorizer.py` uses a keyword lookup
  instead of dressing up an if/else chain as "ML." The dict is structured
  so it's a straightforward swap-in point for a trained classifier once
  you've logged enough real receipts to have labels.
- **Extraction is a draft, not the final answer.** The UI always shows
  OCR confidence and lets you edit every field before saving — auto-
  extraction feeding directly into a ledger with no review step is how
  real expense trackers actually go wrong.

## Architecture

```
Receipt photo (Upload or Camera)
    │
    ▼
gemini_extractor.py   (Gemini Vision LLM: direct multimodal receipt extraction)
    │
    ▼
categorizer.py        (AI category classification + keyword fallback)
    │
    ▼
ledger.py             (pandas + CSV → persistent expense log)
    │
    ▼
app.py                (Streamlit: scan + review tab, dashboard tab, budget tab)
```

## Setup

```bash
pip install -r requirements.txt

# Configure your Gemini API Key in .env:
# GEMINI_API_KEY=your_gemini_api_key_here

streamlit run app.py
```

## Known limitations (worth mentioning honestly in interviews)

- **Item extraction breaks on multi-column layouts** where quantity and
  unit price are separate columns from the line total — the current regex
  assumes "name ... price" on one line. A real fix would use
  `pytesseract.image_to_data` bounding boxes to reconstruct columns
  spatially instead of relying on line-based text.
- **Category rules are keyword-based**, so an unfamiliar vendor name (e.g.
  a local shop not matching any keyword) falls into "Other." This is the
  natural place to add a trained text classifier once there's a labeled
  dataset from real usage.
- **No duplicate detection** — scanning the same receipt twice logs it
  twice. Worth adding a vendor+date+total dedup check.

## Ideas to extend this further

- Add duplicate-receipt detection (hash the image or match vendor+date+total)
- Export the ledger to PDF/Excel for expense reports
- Add a monthly budget per category with over-budget alerts on the dashboard
- Train a small classifier on your own logged receipts to replace the
  keyword-based categorizer — a great "v2" story for an interview
- Deploy on Streamlit Community Cloud for a live demo link

## Sample data

`sample_data/` contains a synthetically generated sample receipt for testing
the pipeline before using your own.
