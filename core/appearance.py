"""Session-based presentation theme; no browser scripting or secrets.

System follows the effective Streamlit client theme (browser/system preference when
Streamlit is set to Use system setting). The local selection is visual, not a
change to Streamlit's global settings.
"""
from __future__ import annotations

PALETTES = {
    "Dark": {
        "app": "#0B1321", "side": "#101C2E", "surface": "#19293E",
        "chart": "#111E30", "border": "#32445B", "text": "#EFF5FC",
        "muted": "#ADC1D8", "accent": "#E3AD59", "heading": "#F9FCFF",
        "badge": "#273951", "badge_text": "#F5CB89", "grid": "#34465B",
        "accent_text": "#142031", "plotly": "plotly_dark", "chart_text": "#DCE7F6",
    },
    "Light": {
        "app": "#F3F6FB", "side": "#FFFFFF", "surface": "#FFFFFF",
        "chart": "#FFFFFF", "border": "#D7E1ED", "text": "#15243B",
        "muted": "#51627A", "accent": "#A86D15", "heading": "#132238",
        "badge": "#FFF1D9", "badge_text": "#74490D", "grid": "#E5EBF3",
        "accent_text": "#FFFFFF", "plotly": "plotly_white", "chart_text": "#364960",
    },
}


def resolve_theme(preference: str, client_theme_type: str | None = None) -> str:
    if preference in ("Light", "Dark"):
        return preference
    return "Light" if client_theme_type == "light" else "Dark"


def stylesheet(mode: str) -> str:
    p = PALETTES[mode]
    # All interpolated values are internal constant hex codes (no user input).
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="css"], .stApp {font-family:'DM Sans',sans-serif;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background: %(app)s !important;color:%(text)s !important;}
[data-testid="stHeader"] {background: %(app)s !important;}
h1,h2,h3,h4 {font-family:'Manrope',sans-serif !important;letter-spacing:-.035em;color:%(heading)s !important;}
p, li, [data-testid="stMarkdownContainer"] {color:inherit;}
.block-container {padding-top:1.25rem;padding-bottom:3.5rem;max-width:1660px;}
[data-testid="stSidebar"] {background:%(side)s !important;border-right:1px solid %(border)s !important;}
[data-testid="stSidebar"] * {overflow-wrap:anywhere;}
[data-testid="stSidebar"] hr {border-color:%(border)s !important;}
[data-testid="stMetric"] {background:%(surface)s !important;border:1px solid %(border)s !important;
   border-radius:17px;padding:17px 19px;min-height:112px;box-shadow:0 5px 25px #00000009;}
[data-testid="stMetricLabel"] {color:%(muted)s !important;}
[data-testid="stMetricValue"] {font-family:'Manrope',sans-serif;font-weight:800;
   font-size:clamp(1.15rem,1.7vw,1.9rem) !important;overflow-wrap:anywhere;white-space:normal !important;line-height:1.25;}
[data-testid="stMetricValue"] div {overflow:visible;}
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {background:%(chart)s;
   border:1px solid %(border)s;border-radius:17px;overflow:hidden;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:%(border)s !important;}
.stButton button[kind="primary"] {background:%(accent)s !important;color:%(accent_text)s !important;
   border:none !important;font-weight:800 !important;border-radius:10px !important;}
button, input, textarea {font-family:'DM Sans',sans-serif !important;}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="base-input"],
[data-testid="stDateInput"] input {border-radius:10px !important;}
.hero {padding:clamp(20px,3vw,38px);border:1px solid %(border)s;
  background:linear-gradient(130deg,%(surface)s,%(app)s);border-radius:20px;margin-bottom:18px;}
.eyebrow {font-size:.77rem;letter-spacing:.14em;font-weight:800;color:%(accent)s;text-transform:uppercase;}
.hero h1 {font-size:clamp(1.65rem,3vw,2.55rem);font-weight:800;margin:.3rem 0;line-height:1.16;color:%(heading)s !important;}
.hero p {font-size:1rem;color:%(muted)s !important;margin:0 0 .5rem;}
.tag {display:inline-block;background:%(badge)s;color:%(badge_text)s;border:1px solid %(border)s;
   border-radius:9px;padding:7px 10px;font-size:.76rem;margin:9px 8px 0 0;font-weight:700;}
.fd-section-header {color:%(heading)s;font-family:'Manrope',sans-serif;font-weight:800;}
[data-testid="stCaptionContainer"] {color:%(muted)s !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {color:%(text)s;}
@media(max-width:880px){.block-container{padding-left:1rem;padding-right:1rem;}
 .hero{padding:22px 18px;}[data-testid="stMetric"]{padding:13px 14px;min-height:95px;}}

/* Native Streamlit elements inherit the ORIGINAL browser theme otherwise.
   Explicit contrast rules are necessary when switching themes at runtime. */
.stApp {
  --text-color: %(text)s;
  --background-color: %(app)s;
  --secondary-background-color: %(surface)s;
  --secondary-text-color: %(muted)s;
  --border-color: %(border)s;
}
/* Streamlit KPI values and their nested numeric spans. */
[data-testid="stMetricValue"], [data-testid="stMetricValue"] *,
[data-testid="stMetricDelta"] {color:%(text)s !important; opacity:1 !important;}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
  color:%(muted)s !important; opacity:1 !important;
}
/* Content and labels from the app's widget framework. */
[data-testid="stMain"] [data-testid="stMarkdownContainer"] > p,
[data-testid="stWidgetLabel"] p,
[data-testid="stRadio"] label p,
[data-testid="stCheckbox"] label p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] > p,
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {
  color:%(text)s !important; opacity:1 !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
  color:%(muted)s !important; opacity:1 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
  background:%(surface)s !important;
  border-radius:9px;
}
/* Theme switcher and filter widgets in the sidebar. */
[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button {
  background:%(surface)s !important;
  color:%(text)s !important;
}
[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"],
[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[data-state="active"] {
  background:%(badge)s !important;
  color:%(badge_text)s !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"] {
  background:%(surface)s !important;
  color:%(text)s !important;
  border-color:%(border)s !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="select"] [role="combobox"] {
  color:%(text)s !important;
}
/* Plotly titles, legends, and axes must use the selected chart theme. */
[data-testid="stPlotlyChart"] .gtitle,
[data-testid="stPlotlyChart"] .xtick text,
[data-testid="stPlotlyChart"] .ytick text,
[data-testid="stPlotlyChart"] .legendtext,
[data-testid="stPlotlyChart"] .xtitle,
[data-testid="stPlotlyChart"] .ytitle {
  fill:%(chart_text)s !important;
  opacity:1 !important;
}

</style>""" % p
