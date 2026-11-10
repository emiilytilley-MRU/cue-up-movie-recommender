import base64
import streamlit as st

# =====================================================================
# CUE UP  |  Movie night, decided.
# Section 1: page setup      Section 2: design system (colours + CSS)
# Section 3: header          Section 4: sidebar filters
# Section 5: main tabs       Section 6: footer
# =====================================================================

# ---------- 1. PAGE SETUP ----------
# The browser tab carries the tagline, so the page itself stays clean
st.set_page_config(
    page_title="Cue Up | Movie night, decided.",
    page_icon="▶",
    layout="wide",
)

# ---------- 2. DESIGN SYSTEM ----------
# One palette, used everywhere (same colours as .streamlit/config.toml)
SLATE = "#334046"
TEAL = "#8AA8B0"
LAVENDER = "#C5B8C8"
PLUM = "#583F57"
TAUPE = "#BBB2AE"
SOFT_WHITE = "#F2EEF3"

MOODS = [
    "Uplifting", "Light & funny", "Romantic", "Bittersweet",
    "Thoughtful", "Adventurous", "Tense", "Dark & heavy",
]

# All styling lives here, so every screen looks like it belongs to one app.
# Rules: one corner radius (16px cards, pill chips), two font weights
# (500 body, 700 headings), and a soft border instead of heavy shadows.
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1180px; }}
footer, #MainMenu {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* Tabs: quiet taupe text, lavender underline on the active tab */
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {TAUPE}33; }}
.stTabs [data-baseweb="tab"] {{ padding: 10px 18px; }}
.stTabs [data-baseweb="tab"] p {{ color: {TAUPE}; font-weight: 500; }}
.stTabs [aria-selected="true"] p {{ color: {LAVENDER}; font-weight: 600; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {LAVENDER}; }}

/* Sidebar: section label style */
.cue-label {{ color: {TAUPE}; font-size: 0.72rem; font-weight: 600;
              letter-spacing: 0.08em; text-transform: uppercase; margin: 4px 0 6px; }}

/* Movie card */
.cue-card {{ display: flex; gap: 20px; background: {PLUM}; border: 1px solid {LAVENDER}2e;
             border-radius: 16px; padding: 20px; margin: 14px 0; }}
.cue-poster {{ flex: 0 0 96px; height: 144px; border-radius: 10px; display: flex;
               align-items: center; justify-content: center; font-size: 1.8rem;
               color: {LAVENDER}; background: linear-gradient(160deg, {SLATE}, #232c30);
               border: 1px solid {TEAL}55; }}
.cue-body {{ flex: 1; min-width: 0; }}
.cue-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }}
.cue-title {{ font-size: 1.2rem; font-weight: 700; color: {SOFT_WHITE}; line-height: 1.25; }}
.cue-meta {{ color: {TAUPE}; font-size: 0.88rem; margin-top: 2px; }}
.cue-rating {{ background: {SLATE}; color: {LAVENDER}; font-weight: 700; font-size: 0.95rem;
               padding: 6px 12px; border-radius: 999px; white-space: nowrap; }}
.cue-chips {{ margin: 12px 0 10px; }}
.cue-chip {{ display: inline-block; padding: 3px 11px; margin: 0 6px 6px 0; border-radius: 999px;
             background: {TEAL}55; color: {SOFT_WHITE}; font-size: 0.78rem; font-weight: 500; }}
.cue-why {{ border-left: 3px solid {TEAL}; padding-left: 12px; color: {SOFT_WHITE}d9;
            font-size: 0.92rem; line-height: 1.5; }}
.cue-watch {{ color: {TAUPE}; font-size: 0.85rem; margin-top: 12px; }}
.cue-watch b {{ color: {SOFT_WHITE}; font-weight: 600; }}

.cue-footer {{ color: {TAUPE}; font-size: 0.78rem; text-align: center; opacity: 0.8;
               border-top: 1px solid {TAUPE}33; padding-top: 16px; margin-top: 40px; }}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- 3. HEADER ----------
# The logo is drawn as SVG (a plum rounded square, teal outline, lavender play symbol)
LOGO_SVG = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 56 56">
  <rect x="2" y="2" width="52" height="52" rx="15" fill="{PLUM}" stroke="{TEAL}" stroke-width="2.5"/>
  <polygon points="22,16 22,40 41,28" fill="{LAVENDER}"/>
</svg>
"""
# Streamlit shows images more reliably when the SVG is encoded as base64 text
logo_b64 = base64.b64encode(LOGO_SVG.encode("utf-8")).decode("utf-8")

st.markdown(
    f"""
<div style="display:flex; align-items:center; gap:14px; padding-bottom:14px; border-bottom:1px solid {TAUPE}33;">
  <img src="data:image/svg+xml;base64,{logo_b64}" width="48" height="48">
  <div style="font-size:2.2rem; font-weight:700; letter-spacing:-0.5px; line-height:1;">
    <span style="color:{LAVENDER};">Cue</span><span style="color:{TEAL};">Up</span>
  </div>
</div>
<p style="color:{TAUPE}; margin:14px 0 18px;">Pick a mood and we'll find tonight's movie.</p>
""",
    unsafe_allow_html=True,
)

# ---------- 4. SIDEBAR FILTERS ----------
# Layout only for now: these widgets get connected to TMDB in a later step
with st.sidebar:
    st.markdown('<div class="cue-label">Filters</div>', unsafe_allow_html=True)
    st.slider("Release years", 1920, 2026, (1990, 2026))
    st.slider("Minimum rating", 0.0, 10.0, 6.5, 0.5)
    st.select_slider("Minimum votes", options=[50, 200, 500, 1000, 5000], value=200)

# ---------- 5. MAIN TABS ----------
tab_mood, tab_similar, tab_trending, tab_insights, tab_search = st.tabs(
    ["Mood Picker", "Find Similar", "Trending", "Insights", "Search"]
)

with tab_mood:
    st.markdown('<div class="cue-label">How are you feeling?</div>', unsafe_allow_html=True)
    st.pills("Mood", MOODS, selection_mode="single", default="Uplifting",
             label_visibility="collapsed")

    # SAMPLE CARD: placeholder text only, shows the layout real results will use
    st.markdown(
        """
<div class="cue-card">
  <div class="cue-poster">▶</div>
  <div class="cue-body">
    <div class="cue-top">
      <div>
        <div class="cue-title">Sample Movie Title</div>
        <div class="cue-meta">2019 &nbsp;·&nbsp; 112 min &nbsp;·&nbsp; PG-13</div>
      </div>
      <div class="cue-rating">★ 7.8</div>
    </div>
    <div class="cue-chips">
      <span class="cue-chip">Comedy</span><span class="cue-chip">Family</span>
      <span class="cue-chip">Mood match 92%</span>
    </div>
    <div class="cue-why">Why this pick: the plot reads warm and hopeful, and it shares genres with your mood.</div>
    <div class="cue-watch"><b>Stream:</b> Netflix, Crave &nbsp;·&nbsp; <b>Rent:</b> Apple TV</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

for tab, name in [(tab_similar, "Find Similar"), (tab_trending, "Trending"),
                  (tab_insights, "Insights"), (tab_search, "Search")]:
    with tab:
        st.caption(f"{name} is being built.")

# ---------- 6. FOOTER ----------
# TMDB's terms ask for this notice wherever its data is shown
st.markdown(
    '<div class="cue-footer">Movie data from TMDB. This product uses the TMDB API but is '
    'not endorsed or certified by TMDB. Streaming availability by JustWatch.</div>',
    unsafe_allow_html=True,
)
