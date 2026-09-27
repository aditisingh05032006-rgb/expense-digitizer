"""
app.py
------
Streamlit front-end for the Expense/Receipt Digitizer.

Three tabs:
  - "Scan Receipt": upload a photo OR use your camera, review/correct
    extracted fields, and save. Warns (but doesn't block) on duplicates.
  - "Dashboard": filterable (via sidebar), interactive Plotly charts,
    an editable table (edit or delete rows inline), CSV/Excel export.
  - "Budgets": set a monthly budget per category, see progress bars.

Run with:  streamlit run app.py
"""

import io
import tempfile
import importlib
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

try:
    import categorizer
    importlib.reload(categorizer)
    from categorizer import categorize, ALL_CATEGORIES
except ImportError:
    try:
        from categorizer import categorize, CATEGORY_KEYWORDS
        ALL_CATEGORIES = list(CATEGORY_KEYWORDS.keys()) + ["Other"]
    except ImportError:
        from categorizer import categorize
        ALL_CATEGORIES = [
            "Food & Dining", "Groceries", "Travel & Transport", "Utilities",
            "Shopping", "Health", "Entertainment", "Other",
        ]

import gemini_extractor
importlib.reload(gemini_extractor)
from gemini_extractor import extract_with_gemini, GeminiExtractionError
from config import GEMINI_ENABLED
from ledger import (
    load_ledger, append_expense, is_duplicate, overwrite_ledger,
    spend_by_category, spend_over_time,
    load_budgets, save_budget, current_month_spend_by_category,
)
import ui_theme
importlib.reload(ui_theme)
from ui_theme import inject_custom_css, page_header, animated_metric

st.set_page_config(page_title="Expense Digitizer", page_icon="🧾", layout="wide")
inject_custom_css()
page_header("🧾 Expense & Receipt Digitizer", "Scan a receipt, track it, stay on budget.")

# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    st.markdown("### Filters")
    st.caption("Applies to the Dashboard tab")
    full_df = load_ledger()

    if not full_df.empty:
        parsed_dates = pd.to_datetime(full_df["timestamp"])
        min_date, max_date = parsed_dates.min().date(), parsed_dates.max().date()
        date_range = st.date_input(
            "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
        )
        selected_categories = st.multiselect(
            "Categories", options=sorted(full_df["category"].unique()),
            default=sorted(full_df["category"].unique()),
        )
    else:
        date_range = None
        selected_categories = []
        st.caption("No data yet — scan a receipt to see filters here.")

tab_scan, tab_dashboard, tab_budgets = st.tabs(["📷 Scan Receipt", "📊 Dashboard", "🎯 Budgets"])

# ---------------------------------------------------------------- Scan tab
with tab_scan:
    if not GEMINI_ENABLED:
        st.warning(
            "⚠️ No Gemini API key found. Add `GEMINI_API_KEY` to your `.env` file to enable receipt digitization."
        )

    input_mode = st.radio("How do you want to add a receipt?", ["Upload a photo", "Use camera"], horizontal=True)

    if input_mode == "Upload a photo":
        uploaded = st.file_uploader("Upload a receipt photo", type=["jpg", "jpeg", "png"])
    else:
        uploaded = st.camera_input("Take a photo of your receipt")

    if uploaded is not None:
        if not GEMINI_ENABLED:
            st.error("Cannot process receipt: Gemini API key is missing. Please configure GEMINI_API_KEY in `.env`.")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read())
                tmp_path = tmp.name

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Receipt")
                st.image(tmp_path, use_container_width=True)

            with st.spinner("Extracting & categorizing receipt with Gemini AI..."):
                try:
                    result = extract_with_gemini(tmp_path)
                    vendor_val = getattr(result, "vendor", "")
                    date_val = getattr(result, "date", "")
                    total_val = getattr(result, "total", 0.0)
                    item_objs = getattr(result, "items", [])
                    ai_category = getattr(result, "category", None)
                    detected_category = categorize(
                        vendor=vendor_val,
                        item_names=[getattr(i, "name", str(i)) for i in item_objs],
                        ai_category=ai_category,
                    )
                    extraction_error = None
                except GeminiExtractionError as e:
                    extraction_error = str(e)
                    vendor_val = ""
                    date_val = ""
                    total_val = 0.0
                    item_objs = []
                    detected_category = "Other"

            with col2:
                st.subheader("Extracted Details")
                if extraction_error:
                    st.error(f"Gemini extraction failed: {extraction_error}")
                else:
                    st.caption(f"✨ Extracted with Gemini AI • Detected Category: **{detected_category}**")

                vendor = st.text_input("Vendor", value=vendor_val or "")
                date = st.text_input("Date", value=date_val or "")
                total = st.number_input("Total", value=float(total_val or 0.0), step=0.01)
                category = st.selectbox(
                    "Category (auto-detected)",
                    options=ALL_CATEGORIES,
                    index=ALL_CATEGORIES.index(detected_category) if detected_category in ALL_CATEGORIES else ALL_CATEGORIES.index("Other"),
                    help="Automatically detected by Gemini AI from the receipt content.",
                )

                if item_objs:
                    st.caption("Detected line items:")
                    items_df = pd.DataFrame([{"item": i.name, "price": i.price} for i in item_objs])
                    st.dataframe(items_df, hide_index=True, use_container_width=True)

                duplicate_found = is_duplicate(vendor, date, total)
                if duplicate_found:
                    st.warning(
                        "⚠️ A receipt with this same vendor, date, and total is already "
                        "logged. Saving again will create a duplicate entry."
                    )
                    confirm_dup = st.checkbox("Save anyway")
                else:
                    confirm_dup = True

                if st.button("💾 Save to ledger", type="primary", disabled=not confirm_dup):
                    item_names = [i.name for i in item_objs]
                    append_expense(vendor, date, category, total, item_names, "Gemini AI")
                    st.success(f"Saved ₹{total:.2f} at {vendor} under {category}.")
    else:
        st.info("👆 Upload a receipt or use your camera to extract fields automatically.")

# ------------------------------------------------------------- Dashboard tab
with tab_dashboard:
    df = load_ledger()

    if df.empty:
        st.info("No expenses logged yet. Scan a receipt in the first tab to get started.")
    else:
        # Apply sidebar filters
        filtered = df.copy()
        parsed_dates = pd.to_datetime(filtered["timestamp"])
        if date_range and len(date_range) == 2:
            start, end = date_range
            mask = (parsed_dates.dt.date >= start) & (parsed_dates.dt.date <= end)
            filtered = filtered[mask]
        if selected_categories:
            filtered = filtered[filtered["category"].isin(selected_categories)]

        if filtered.empty:
            st.warning("No expenses match the current filters.")
        else:
            total_spend = filtered["total"].sum()
            m1, m2, m3 = st.columns(3)
            with m1:
                animated_metric("Total logged", total_spend, prefix="₹")
            with m2:
                animated_metric("Receipts", len(filtered), prefix="", decimals=0)
            with m3:
                animated_metric("Avg. per receipt", total_spend / len(filtered), prefix="₹")

            st.write("")
            c1, c2 = st.columns(2)

            cat_series = spend_by_category(filtered)
            time_series = spend_over_time(filtered)

            # ── Animated bar chart (spend by category) ──────────────────────
            with c1:
                st.subheader("Spend by category")
                cat_labels = [str(x) for x in cat_series.index.tolist()]
                cat_values = [float(x) for x in cat_series.values.tolist()]
                bar_chart_html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    background: transparent;
    font-family: 'Inter', sans-serif;
    padding: 4px;
}}
.chart-box {{
    background: linear-gradient(135deg, rgba(38, 19, 10, 0.90), rgba(52, 26, 14, 0.90));
    backdrop-filter: blur(18px);
    border: 1.5px solid rgba(255, 255, 255, 0.3);
    border-radius: 16px;
    padding: 1.1rem;
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.45), 0 0 1px rgba(255, 255, 255, 0.15) inset;
    transition: transform 0.25s ease, border-color 0.25s, box-shadow 0.25s;
}}
.chart-box:hover {{
    border-color: #FFAA80;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55), 0 0 20px rgba(245, 158, 11, 0.25);
    transform: translateY(-3px);
}}
canvas {{ border-radius: 10px; }}
</style>
</head><body>
<div class="chart-box">
<canvas id="barChart"></canvas>
</div>
<script>
const ctx = document.getElementById('barChart').getContext('2d');
const grad = ctx.createLinearGradient(0, 0, 400, 0);
grad.addColorStop(0, '#F59E0B');
grad.addColorStop(1, '#E06D36');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: {cat_labels},
    datasets: [{{
      label: 'Amount (₹)',
      data: {cat_values},
      backgroundColor: grad,
      borderRadius: 8,
      borderSkipped: false,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    animation: {{ duration: 900, easing: 'easeOutQuart' }},
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: '#2A140A',
        titleColor: '#FFFFFF',
        bodyColor: '#FFD8BF',
        borderColor: '#E06D36',
        borderWidth: 1.5,
        padding: 10,
        callbacks: {{
          label: ctx => ' ₹' + ctx.parsed.x.toFixed(2)
        }}
      }}
    }},
    scales: {{
      x: {{
        grid: {{ color: 'rgba(255,255,255,0.1)' }},
        ticks: {{ color: '#FFFFFF', font: {{ family: 'Inter, sans-serif', size: 12 }} }},
        border: {{ color: 'rgba(255,255,255,0.2)' }}
      }},
      y: {{
        grid: {{ display: false }},
        ticks: {{ color: '#FFFFFF', font: {{ family: 'Inter, sans-serif', size: 12 }} }},
        border: {{ color: 'rgba(255,255,255,0.2)' }}
      }}
    }}
  }}
}});
</script></body></html>
"""
                components.html(bar_chart_html, height=max(220, len(cat_labels) * 54 + 60))

            # ── Animated line graph (spend over time) ────────────────────────
            with c2:
                st.subheader("Spend over time")
                time_labels = [str(d) for d in time_series.index.tolist()]
                time_values = [float(v) for v in time_series.values.tolist()]
                line_chart_html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    background: transparent;
    font-family: 'Inter', sans-serif;
    padding: 4px;
}}
.chart-box {{
    background: linear-gradient(135deg, rgba(38, 19, 10, 0.90), rgba(52, 26, 14, 0.90));
    backdrop-filter: blur(18px);
    border: 1.5px solid rgba(255, 255, 255, 0.3);
    border-radius: 16px;
    padding: 1.1rem;
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.45), 0 0 1px rgba(255, 255, 255, 0.15) inset;
    transition: transform 0.25s ease, border-color 0.25s, box-shadow 0.25s;
}}
.chart-box:hover {{
    border-color: #FFAA80;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55), 0 0 20px rgba(245, 158, 11, 0.25);
    transform: translateY(-3px);
}}
canvas {{ border-radius: 10px; }}
</style>
</head><body>
<div class="chart-box">
<canvas id="lineChart"></canvas>
</div>
<script>
const lctx = document.getElementById('lineChart').getContext('2d');
const lineGrad = lctx.createLinearGradient(0, 0, 0, 280);
lineGrad.addColorStop(0, 'rgba(224, 109, 54, 0.45)');
lineGrad.addColorStop(1, 'rgba(224, 109, 54, 0.0)');
new Chart(lctx, {{
  type: 'line',
  data: {{
    labels: {time_labels},
    datasets: [{{
      label: 'Amount (₹)',
      data: {time_values},
      borderColor: '#E06D36',
      borderWidth: 3,
      backgroundColor: lineGrad,
      fill: true,
      tension: 0.42,
      pointBackgroundColor: '#F59E0B',
      pointBorderColor: '#FFFFFF',
      pointBorderWidth: 2.5,
      pointRadius: 6,
      pointHoverRadius: 9,
      pointHoverBackgroundColor: '#FFFFFF',
      pointHoverBorderColor: '#E06D36',
    }}]
  }},
  options: {{
    animation: {{
      duration: 1000,
      easing: 'easeOutQuart',
    }},
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: '#2A140A',
        titleColor: '#FFFFFF',
        bodyColor: '#FFD8BF',
        borderColor: '#E06D36',
        borderWidth: 1.5,
        padding: 10,
        callbacks: {{
          label: ctx => ' ₹' + ctx.parsed.y.toFixed(2)
        }}
      }}
    }},
    scales: {{
      x: {{
        grid: {{ color: 'rgba(255,255,255,0.1)' }},
        ticks: {{ color: '#FFFFFF', font: {{ family: 'Inter, sans-serif', size: 11 }}, maxRotation: 30 }},
        border: {{ color: 'rgba(255,255,255,0.2)' }}
      }},
      y: {{
        grid: {{ color: 'rgba(255,255,255,0.1)' }},
        ticks: {{
          color: '#FFFFFF',
          font: {{ family: 'Inter, sans-serif', size: 12 }},
          callback: v => '₹' + v.toLocaleString()
        }},
        border: {{ color: 'rgba(255,255,255,0.2)' }}
      }}
    }}
  }}
}});
</script></body></html>
"""
                components.html(line_chart_html, height=340)

            st.subheader("All expenses (double-click a cell to edit)")
            st.caption("⚡ Cell edits save automatically. Check the box and click 'Delete' to remove rows manually.")

            editable = filtered[["date", "vendor", "category", "total", "ocr_confidence"]].copy()
            editable.insert(0, "Delete?", False)

            if "editor_version" not in st.session_state:
                st.session_state["editor_version"] = 0
            editor_key = f"ledger_editor_{st.session_state['editor_version']}"

            edited = st.data_editor(
                editable,
                use_container_width=True,
                hide_index=False,
                column_config={
                    "category": st.column_config.SelectboxColumn(options=ALL_CATEGORIES),
                    "ocr_confidence": st.column_config.TextColumn("Source / Method"),
                    "Delete?": st.column_config.CheckboxColumn("Delete?", help="Select row to delete manually"),
                },
                key=editor_key,
            )

            content_cols = ["date", "vendor", "category", "total", "ocr_confidence"]
            delete_selected = edited[edited["Delete?"]].index.tolist()

            # 1. Automatically apply cell edits (vendor, date, category, total)
            if not edited[content_cols].equals(editable[content_cols]):
                full_df = load_ledger()
                full_df.update(edited[content_cols])
                overwrite_ledger(full_df)
                st.session_state["editor_version"] += 1
                st.toast("Cell changes auto-saved! 💾", icon="✅")
                st.rerun()

            # 2. Manual button for deleting selected rows
            if delete_selected:
                count = len(delete_selected)
                del_btn_text = f"🗑️ Delete {count} selected expense{'s' if count > 1 else ''}"
                col_del, _ = st.columns([3, 7])
                with col_del:
                    if st.button(del_btn_text, type="primary"):
                        full_df = load_ledger()
                        full_df = full_df.drop(index=delete_selected, errors="ignore")
                        overwrite_ledger(full_df)
                        st.session_state["editor_version"] += 1
                        st.toast(f"Deleted {count} expense{'s' if count > 1 else ''}.", icon="🗑️")
                        st.rerun()

            st.subheader("Export")
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                csv_bytes = filtered.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download as CSV", data=csv_bytes,
                    file_name="expenses_ledger.csv", mime="text/csv",
                )
            with exp_col2:
                excel_buffer = io.BytesIO()
                filtered.to_excel(excel_buffer, index=False, sheet_name="Expenses")
                st.download_button(
                    "⬇️ Download as Excel", data=excel_buffer.getvalue(),
                    file_name="expenses_ledger.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

# --------------------------------------------------------------- Budgets tab
with tab_budgets:
    st.subheader("Set a monthly budget per category")
    budgets = load_budgets()

    budget_col1, budget_col2 = st.columns([2, 1])
    with budget_col1:
        budget_category = st.selectbox("Category", options=ALL_CATEGORIES, key="budget_cat")
    with budget_col2:
        existing = budgets.get(budget_category, 0.0)
        new_amount = st.number_input("Monthly budget (₹)", value=float(existing), step=100.0, key="budget_amt")

    if st.button("Save budget"):
        save_budget(budget_category, new_amount)
        st.success(f"Budget for {budget_category} set to ₹{new_amount:,.2f}/month.")
        st.rerun()

    st.divider()
    st.subheader("This month vs. your budgets")

    df = load_ledger()
    budgets = load_budgets()
    if not budgets:
        st.info("No budgets set yet — add one above to see progress here.")
    else:
        month_spend = current_month_spend_by_category(df)

        # Build HTML for all budget cards in one component
        cards_html = []
        for category, budget_amount in budgets.items():
            spent = float(month_spend.get(category, 0.0))
            pct = min(spent / budget_amount, 1.0) if budget_amount > 0 else 0.0
            spent_pct = round(pct * 100, 1)
            remaining = max(budget_amount - spent, 0.0)
            over_budget = budget_amount > 0 and spent > budget_amount
            over_by = spent - budget_amount if over_budget else 0.0

            over_badge = (
                f'<span class="budget-over-badge">⚠ OVER BY ₹{over_by:,.0f}</span>'
                if over_budget else
                f'<span class="budget-ok-badge">₹{remaining:,.0f} left</span>'
            )
            card = f"""
            <div class="budget-card {'budget-card-over' if over_budget else ''}">
                <div class="budget-card-header">
                    <span class="budget-cat-name">{category}</span>
                    {over_badge}
                </div>
                <div class="budget-amounts">
                    <span class="spent-label">Spent <strong>₹{spent:,.0f}</strong></span>
                    <span class="total-label">of ₹{budget_amount:,.0f}</span>
                    <span class="budget-pct-label">{spent_pct}%</span>
                </div>
                <div class="budget-track">
                    <div class="budget-spent-bar" style="width:{spent_pct}%"></div>
                </div>
            </div>
            """
            cards_html.append(card)

        full_html = f"""
        <!DOCTYPE html><html><head>
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: transparent; font-family: 'Inter', sans-serif; padding: 4px 2px 8px; }}

        .budget-card {{
            background: linear-gradient(135deg, rgba(15,8,3,0.95) 0%, rgba(30,12,3,0.90) 100%);
            border: 1.5px solid rgba(255,120,30,0.30);
            border-radius: 16px;
            padding: 18px 22px 20px;
            margin-bottom: 16px;
            box-shadow:
                0 0 0 1px rgba(255,80,0,0.08),
                0 4px 24px rgba(0,0,0,0.7),
                0 0 40px rgba(255,100,20,0.08) inset;
            position: relative;
            overflow: visible;
            transition: box-shadow 0.3s ease, border-color 0.3s ease;
        }}
        .budget-card:hover {{
            border-color: rgba(255,140,30,0.60);
            box-shadow:
                0 0 0 1px rgba(255,100,0,0.15),
                0 8px 32px rgba(0,0,0,0.75),
                0 0 60px rgba(255,110,20,0.14) inset;
        }}
        .budget-card-over {{
            border-color: rgba(255,60,0,0.55) !important;
            animation: pulse-over 2s ease-in-out infinite;
        }}
        @keyframes pulse-over {{
            0%, 100% {{ box-shadow: 0 0 0 1px rgba(255,40,0,0.2), 0 4px 24px rgba(0,0,0,0.7), 0 0 30px rgba(255,40,0,0.12) inset; }}
            50%       {{ box-shadow: 0 0 0 2px rgba(255,40,0,0.5), 0 4px 32px rgba(0,0,0,0.8), 0 0 55px rgba(255,40,0,0.25) inset; }}
        }}

        .budget-card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        .budget-cat-name {{
            font-family: 'Poppins', sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: 0.01em;
        }}
        .budget-ok-badge {{
            font-size: 0.72rem;
            font-weight: 600;
            color: #F59E0B;
            background: rgba(245,158,11,0.12);
            border: 1px solid rgba(245,158,11,0.35);
            border-radius: 999px;
            padding: 3px 10px;
            letter-spacing: 0.04em;
        }}
        .budget-over-badge {{
            font-size: 0.72rem;
            font-weight: 700;
            color: #FF6030;
            background: rgba(255,60,0,0.14);
            border: 1px solid rgba(255,60,0,0.45);
            border-radius: 999px;
            padding: 3px 10px;
            letter-spacing: 0.04em;
            animation: badge-flash 1.4s ease-in-out infinite;
        }}
        @keyframes badge-flash {{
            0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.55; }}
        }}

        .budget-amounts {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 12px;
        }}
        .spent-label {{
            font-size: 0.88rem;
            color: #FFC080;
        }}
        .spent-label strong {{
            font-size: 1.15rem;
            font-weight: 700;
            color: #FFFFFF;
        }}
        .total-label {{
            font-size: 0.82rem;
            color: rgba(255,200,150,0.55);
        }}
        .budget-pct-label {{
            margin-left: auto;
            font-size: 0.88rem;
            font-weight: 700;
            color: #F59E0B;
            text-shadow: 0 0 10px rgba(245,158,11,0.85);
            letter-spacing: 0.03em;
            white-space: nowrap;
        }}

        /* The track */
        .budget-track {{
            position: relative;
            width: 100%;
            height: 18px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(245,158,11,0.22) 100%);
            border: 1px solid rgba(245,158,11,0.20);
            overflow: hidden;
        }}

        /* Spent = BLACK GLOW bar */
        .budget-spent-bar {{
            position: absolute;
            top: 0; left: 0;
            height: 100%;
            border-radius: 999px;
            min-width: 8px;
            background: linear-gradient(90deg, #0A0A0A 0%, #1C1C1C 40%, #2A1500 100%);
            box-shadow:
                0 0 12px 3px rgba(0, 0, 0, 0.95),
                0 0 22px 6px rgba(20, 8, 0, 0.75),
                inset 0 1px 0 rgba(255,255,255,0.08);
            border: 1px solid rgba(255,90,0,0.25);
            transition: width 1.1s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        /* Remaining = implied orange glow from the track glow effect */
        .budget-track::after {{
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 100%;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, transparent 0%, rgba(230,100,20,0.18) 60%, rgba(245,158,11,0.35) 100%);
            pointer-events: none;
        }}


        </style>
        </head>
        <body>
        {''.join(cards_html)}
        </body></html>
        """

        import streamlit.components.v1 as components
        components.html(full_html, height=len(budgets) * 130 + 20, scrolling=False)
