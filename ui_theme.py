"""
ui_theme.py
-----------
Editorial Terracotta & Warm Aesthetic Design System:
- Pure orange radial gradient background (no photos, no doodles).
- Applied directly to [data-testid="stAppViewContainer"] with transparent main container.
- Geometric orange hexagon finance logo (no people, no flowers).
- Interactive 3D metric cards with mouse-tracking tilt, lighting glare, and count-up easing.
"""

import base64
import pathlib

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Pre-load logo as base64 data URI — renders instantly, no HTTP round-trip
# ---------------------------------------------------------------------------
_LOGO_PATH = pathlib.Path(__file__).parent / "static" / "fancy_logo_thumb.jpg"
try:
    _LOGO_B64 = "data:image/jpeg;base64," + base64.b64encode(_LOGO_PATH.read_bytes()).decode()
except Exception:
    _LOGO_B64 = "/app/static/fancy_logo_thumb.jpg"  # fallback

# ---------------------------------------------------------------------------
# Master CSS styling with Terracotta Background, Glassmorphism & High Contrast
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

/* --- Base & Terracotta App Viewport --- */
html, body, [data-testid="stApp"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #FFFFFF !important;
}

/* Apply background directly to Streamlit's actual scroll container */
[data-testid="stAppViewContainer"] {
    background-color: #7A2E0A !important;
    background-image: 
        radial-gradient(ellipse at 20% 0%, #E05C20 0%, #B04010 35%, #7A2E0A 65%, #4A1A04 100%) !important;
    background-size: 100% 100% !important;
    background-attachment: fixed !important;
}

/* Transparent Header & Main Content Area so background shines through */
[data-testid="stHeader"] {
    background-color: transparent !important;
}

[data-testid="stMain"] {
    background-color: transparent !important;
}

[data-testid="stMainBlockContainer"], .block-container {
    padding-top: 3.25rem !important;
    padding-bottom: 4rem !important;
}

/* --- Typography (Clean High-Contrast White & Warm Cream) --- */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Poppins', sans-serif !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}

p, span, label, div, td, th {
    color: #FFFFFF;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: #F5EBE1 !important;
    font-weight: 500;
}

/* --- Section Heading Underline Accent --- */
h2, h3 {
    position: relative;
    padding-bottom: 0.35rem;
}

h2::after, h3::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 52px;
    height: 3px;
    border-radius: 99px;
    background: linear-gradient(90deg, #FFFFFF, #F59E0B);
    transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

h2:hover::after, h3:hover::after {
    width: 95px;
}

/* --- Pop-in entrance animation + accent line for boxes (uploader, alerts,
   expanders, tables) — matches the underline accent style used on headings
   like "Filters", so boxes across Scan/Dashboard/Budgets feel consistent
   with the sidebar instead of just appearing flat. --- */
@keyframes popIn {
    0% {
        opacity: 0;
        transform: translateY(16px) scale(0.97);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

[data-testid="stAlert"],
[data-testid="stFileUploader"],
[data-testid="stExpander"],
[data-testid="stDataEditor"],
[data-testid="stDataFrame"],
[data-testid="stMetric"] {
    animation: popIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Stagger successive boxes slightly so they don't all pop at once */
[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:nth-child(2) [data-testid="stAlert"] { animation-delay: 0.05s; }
[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:nth-child(3) [data-testid="stAlert"] { animation-delay: 0.1s; }
[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:nth-child(4) [data-testid="stAlert"] { animation-delay: 0.15s; }

/* Orange underline-only on alert/info/warning/success — no box, just the line */
[data-testid="stAlert"] {
    position: relative;
    overflow: hidden;
    border-radius: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding-left: 0 !important;
    padding-top: 0.75rem !important;
}

[data-testid="stAlert"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 52px;
    height: 3px;
    border-radius: 99px;
    background: linear-gradient(90deg, #FFFFFF, #F59E0B);
    transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

[data-testid="stAlert"]:hover::before {
    width: 95px;
}

/* Same accent line on the file uploader box and expanders */
[data-testid="stFileUploader"],
[data-testid="stExpander"] {
    position: relative;
    overflow: hidden;
}

[data-testid="stFileUploader"]::before,
[data-testid="stExpander"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 52px;
    height: 3px;
    border-radius: 99px;
    background: linear-gradient(90deg, #FFFFFF, #F59E0B);
    transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 2;
}

[data-testid="stFileUploader"]:hover::before,
[data-testid="stExpander"]:hover::before {
    width: 95px;
}

/* --- Header Title with Warm Cream-to-Gold Shimmer --- */
.gradient-title-wrap {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    margin-bottom: 0.4rem;
}

.gradient-title-text {
    background: linear-gradient(135deg, #FFFFFF 0%, #FFF3EA 35%, #FFB68D 70%, #F59E0B 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.15;
    filter: drop-shadow(0 2px 10px rgba(0,0,0,0.5));
}

.header-subtitle {
    color: #FDF6ED !important;
    font-size: 1.05rem;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    text-shadow: 0 1px 4px rgba(0,0,0,0.5);
    padding-right: 160px;  /* keeps badges away from Streamlit toolbar */
    max-width: 100%;
}

/* Feature badges in header */
.header-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.22rem 0.7rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(40, 20, 10, 0.75);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #FFF1E6 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #F59E0B;
    box-shadow: 0 0 8px #F59E0B;
}

/* --- Fancy 3D Luxury Logo Styling --- */
.fancy-logo-container {
    perspective: 800px;
    display: inline-flex;
    align-items: center;
}

.fancy-logo {
    width: 74px;
    height: 74px;
    object-fit: cover;
    border-radius: 20px;
    border: 2px solid rgba(255, 220, 180, 0.55);
    box-shadow: 
        0 12px 28px rgba(0, 0, 0, 0.65),
        0 0 24px rgba(245, 158, 11, 0.35),
        0 0 0 1px rgba(255, 255, 255, 0.25) inset;
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
    background: #1C0F08;
    transform: perspective(600px) rotate(-3deg) rotateY(6deg);
}

.fancy-logo:hover {
    transform: perspective(600px) rotate(0deg) scale(1.15) translateY(-6px);
    box-shadow: 
        0 20px 42px rgba(0, 0, 0, 0.75),
        0 0 35px rgba(245, 158, 11, 0.6),
        0 0 0 1px rgba(255, 255, 255, 0.6) inset;
    border-color: #FFAA80;
}

/* --- Navigation Tabs — underline-only, no boxes --- */
/* Hide BaseWeb default built-in active tab highlight bar & bottom border (prevents overlapping lines) */
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent !important;
    backdrop-filter: none;
    padding: 0;
    border-radius: 0;
    border: none;
    box-shadow: none;
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.15);
    margin-bottom: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    height: auto;
    padding: 0.65rem 1.25rem 0.75rem;
    border-radius: 0;
    font-weight: 600;
    font-size: 0.95rem;
    color: rgba(232, 213, 196, 0.7) !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    position: relative;
    transition: color 0.22s ease, transform 0.22s ease;
}

/* Orange underline — matching the Filters heading style (left-aligned gradient line) */
.stTabs [data-baseweb="tab"]::after {
    content: '';
    position: absolute;
    bottom: -1.5px;
    left: 1.25rem;
    width: 0;
    height: 3px;
    border-radius: 99px;
    background: linear-gradient(90deg, #FFFFFF, #F59E0B);
    transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Hover — text pops up, orange line pops in like Filters */
.stTabs [data-baseweb="tab"]:hover {
    color: #FFFFFF !important;
    background: transparent !important;
    transform: translateY(-2px);
}

.stTabs [data-baseweb="tab"]:hover::after {
    width: 52px;
}

/* Active — orange underline (52px wide, matching Filters heading) */
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: none !important;
    transform: translateY(-2px);
    text-shadow: 0 0 16px rgba(245, 158, 11, 0.5);
}

.stTabs [aria-selected="true"]::after {
    width: 52px;
}

.stTabs [aria-selected="true"]:hover::after {
    width: 95px;
}


/* --- Data Editor & Tables High Visibility --- */
[data-testid="stDataEditor"], [data-testid="stDataFrame"], [data-testid="stTable"] {
    background: rgba(30, 15, 8, 0.88) !important;
    backdrop-filter: blur(18px);
    border: 1.5px solid rgba(255, 255, 255, 0.28) !important;
    border-radius: 14px !important;
    overflow: hidden;
    color: #FFFFFF !important;
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.45);
}

[data-testid="stDataEditor"] div, [data-testid="stDataFrame"] div,
[data-testid="stDataEditor"] span, [data-testid="stDataFrame"] span {
    color: #FFFFFF !important;
}

/* --- Buttons with Warm Terracotta & Amber Glaze --- */
.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    letter-spacing: 0.01em;
    padding: 0.55rem 1.4rem;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    color: #FFFFFF !important;
    background: linear-gradient(135deg, #E06D36, #B05520) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 4px 18px rgba(176, 85, 32, 0.45);
}

.stButton > button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 28px rgba(224, 109, 54, 0.65), 0 0 14px rgba(255, 255, 255, 0.3) !important;
    border-color: rgba(255, 255, 255, 0.7) !important;
}

.stButton > button:active {
    transform: translateY(1px) scale(0.98);
}

/* Secondary / Download Buttons */
[data-testid="stDownloadButton"] > button {
    border-radius: 12px;
    font-weight: 600;
    background: rgba(40, 20, 10, 0.88) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.3) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
    transition: all 0.2s ease;
}

[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, rgba(224, 109, 54, 0.4), rgba(176, 85, 32, 0.4)) !important;
    border-color: #FFAA80 !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(224, 109, 54, 0.4) !important;
}

/* --- Input Fields & Select Boxes --- */
input[type="text"], input[type="number"], .stSelectbox div[data-baseweb="select"] {
    background: rgba(38, 19, 10, 0.88) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
    transition: all 0.2s ease;
}

input[type="text"]:focus, input[type="number"]:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
    border-color: #FFAA80 !important;
    box-shadow: 0 0 16px rgba(224, 109, 54, 0.5) !important;
}

/* File Uploader — borderless, just orange underline at top */
[data-testid="stFileUploader"] {
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    backdrop-filter: none;
    padding: 0.5rem 0 1rem;
}

[data-testid="stFileUploader"]:hover {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: rgba(30, 15, 8, 0.94) !important;
    backdrop-filter: blur(20px);
    border-right: 1.5px solid rgba(255, 255, 255, 0.2) !important;
}

/* Progress bar */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #F59E0B, #E06D36) !important;
    border-radius: 99px !important;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.5);
}

/* Hide "Made with Streamlit" footer */
footer, [data-testid="stBottom"], #MainMenu {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #5A270D;
}
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #E06D36, #F59E0B);
    border-radius: 8px;
}
::-webkit-scrollbar-thumb:hover {
    background: #FFAA80;
}
</style>
"""


def inject_custom_css():
    """Injects master design tokens with user-uploaded wallpaper background."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def page_header(title: str = "Expense & Receipt Digitizer", subtitle: str = ""):
    """
    Renders header with:
    - Real paper receipt hero graphic (with realistic paper crinkle, tilt, and physics shadow)
    - Shimmering warm cream-to-gold typography
    - Editorial status badges
    """
    clean_title = title.replace("🧾", "").strip()

    img_html = f'<div class="fancy-logo-container" title="Expense Digitizer • Powered by Gemini AI"><img class="fancy-logo" src="{_LOGO_B64}" alt="Expense Digitizer Logo" decoding="sync"></div>'

    header_html = (
        '<div style="margin-top: 0; margin-bottom: 1.2rem;">'
        '<div class="gradient-title-wrap">'
        f'{img_html}'
        '<div>'
        f'<div class="gradient-title-text">{clean_title}</div>'
        '</div>'
        '</div>'
        '<div class="header-subtitle">'
        f'<span>{subtitle or "Scan a receipt, track it, stay on budget."}</span>'
        '<span class="header-badge"><span class="pulse-dot"></span> REAL PAPER • AI DIGITIZED</span>'
        '<span class="header-badge">⚡ AUTO-SAVE ACTIVE</span>'
        '</div>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)


def animated_metric(label: str, value: float, prefix: str = "₹", decimals: int = 2, height: int = 125):
    """
    3D glassmorphic metric card with:
    - Warm terracotta & dark glass aesthetics with crisp white photo-frame borders
    - Interactive 3D mouse tilt tracking (perspective X & Y rotation)
    - Glare reflection following cursor coordinates
    - Count-up number animation via requestAnimationFrame
    """
    element_id = f"counter-{abs(hash(label))}"
    card_id = f"card-{abs(hash(label))}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@500;600;700&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: transparent;
        font-family: 'Inter', sans-serif;
        overflow: hidden;
        padding: 4px;
    }}
    .metric-card-3d {{
        position: relative;
        background: linear-gradient(135deg, rgba(38, 19, 10, 0.90), rgba(52, 26, 14, 0.90));
        backdrop-filter: blur(18px);
        border: 1.5px solid rgba(255, 255, 255, 0.32);
        border-radius: 16px;
        padding: 1.1rem 1.35rem;
        box-shadow: 
            0 8px 30px rgba(0, 0, 0, 0.45),
            0 0 1px rgba(255, 255, 255, 0.25) inset;
        transform-style: preserve-3d;
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s, border-color 0.25s;
        cursor: default;
        overflow: hidden;
    }}
    .metric-card-3d:hover {{
        border-color: #FFAA80;
        box-shadow: 
            0 16px 36px rgba(0, 0, 0, 0.55),
            0 0 24px rgba(245, 158, 11, 0.35),
            0 0 1px rgba(255, 255, 255, 0.5) inset;
    }}
    .glare {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 16px;
        background: radial-gradient(circle at 50% 50%, rgba(255,255,255,0.18) 0%, transparent 60%);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s;
    }}
    .metric-card-3d:hover .glare {{
        opacity: 1;
    }}
    .metric-label {{
        color: #FFD8BF !important;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .metric-value {{
        font-family: 'Poppins', sans-serif;
        font-size: 1.95rem;
        font-weight: 700;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 14px rgba(0, 0, 0, 0.5);
        transition: text-shadow 0.3s;
    }}
    .metric-card-3d:hover .metric-value {{
        text-shadow: 0 0 24px rgba(245, 158, 11, 0.6);
    }}
    </style>
    </head>
    <body>
    <div class="metric-card-3d" id="{card_id}">
        <div class="glare" id="glare-{card_id}"></div>
        <div class="metric-label">{label}</div>
        <div class="metric-value" id="{element_id}">{prefix}0</div>
    </div>
    <script>
    (function() {{
        const target = {value};
        const el = document.getElementById("{element_id}");
        const duration = 850;
        const start = performance.now();

        function step(now) {{
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4);
            const current = target * eased;
            el.textContent = "{prefix}" + current.toLocaleString(undefined, {{
                minimumFractionDigits: {decimals},
                maximumFractionDigits: {decimals}
            }});
            if (progress < 1) {{
                requestAnimationFrame(step);
            }}
        }}
        requestAnimationFrame(step);

        const card = document.getElementById("{card_id}");
        const glare = document.getElementById("glare-{card_id}");

        card.addEventListener("mousemove", (e) => {{
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -10;
            const rotateY = ((x - centerX) / centerX) * 12;

            card.style.transform = `perspective(600px) rotateX(${{rotateX}}deg) rotateY(${{rotateY}}deg) translateY(-5px)`;
            glare.style.background = `radial-gradient(circle at ${{x}}px ${{y}}px, rgba(255,255,255,0.22) 0%, transparent 60%)`;
        }});

        card.addEventListener("mouseleave", () => {{
            card.style.transform = "perspective(600px) rotateX(0deg) rotateY(0deg) translateY(0)";
            glare.style.background = "";
        }});
    }})();
    </script>
    </body>
    </html>
    """
    components.html(html, height=height)
