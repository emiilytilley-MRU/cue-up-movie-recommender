import base64
import datetime as dt

import pandas as pd
import streamlit as st

# =====================================================================
# CUE UP  |  Movie night, decided.
# Section 1: page setup      Section 2: design system (colours + CSS)
# Section 3: header          Section 4: sidebar filters
# Section 5: watched history Section 6: main tabs
# Section 7: footer
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

# One line per mood, shown under the picker so people know what they are choosing
MOOD_NOTES = {
    "Uplifting": "Warm, hopeful stories. Comedy, family and music.",
    "Light & funny": "Easy and silly. Comedy and animation.",
    "Romantic": "Love stories with a happy tilt.",
    "Bittersweet": "Love and loss together. Romance with drama.",
    "Thoughtful": "Slower and more reflective. Drama and documentary.",
    "Adventurous": "Big worlds, big stakes. Adventure, fantasy, sci-fi and action.",
    "Tense": "Edge of your seat. Thriller and mystery.",
    "Dark & heavy": "Serious and intense. Crime, war and horror.",
}

# How you feel right now -> (the vibe we start you on, a second one to try)
FEELINGS = {
    "Stressed": ("Light & funny", "Uplifting"),
    "Sad": ("Uplifting", "Bittersweet"),
    "Tired": ("Light & funny", "Romantic"),
    "Bored": ("Adventurous", "Tense"),
    "Lonely": ("Romantic", "Uplifting"),
    "Happy": ("Adventurous", "Light & funny"),
    "Calm": ("Thoughtful", "Romantic"),
}

# Choices for the sidebar filters (these get wired to TMDB in a later step)
GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama",
    "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance",
    "Science Fiction", "Thriller", "War", "Western",
]
DECADES = ["Any", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
RUNTIMES = ["Any length", "Under 90 min", "90 to 120 min", "Over 120 min"]
CERTIFICATIONS = ["G", "PG", "PG-13", "R", "NC-17"]
# Language name -> the two-letter code TMDB expects
LANGUAGES = {
    "Any": None, "English": "en", "French": "fr", "Spanish": "es", "Korean": "ko",
    "Japanese": "ja", "Hindi": "hi", "German": "de", "Italian": "it",
}

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

/* One-line explanation under the vibe picker */
.cue-note {{ color: {TAUPE}; font-size: 0.9rem; margin: 10px 0 4px; }}
.cue-note b {{ color: {LAVENDER}; font-weight: 600; }}

/* Vibe pills: the chosen one fills with teal and uses dark text */
button[data-variant="pills"] {{ border-radius: 999px; }}
button[data-variant="pills"][aria-checked="true"] {{ background-color: {TEAL} !important; border-color: {TEAL} !important; }}
button[data-variant="pills"][aria-checked="true"] p {{ color: {SLATE} !important; font-weight: 600; }}

/* One row in the History tab */
.cue-hist-title {{ color: {SOFT_WHITE}; font-weight: 600; }}
.cue-hist-meta {{ color: {TAUPE}; font-size: 0.88rem; }}

/* Primary buttons: dark text on teal so the label is easy to read */
.stButton button[kind="primary"] {{ border: none; border-radius: 10px; }}
.stButton button[kind="primary"] p {{ color: {SLATE}; font-weight: 600; }}

/* Sidebar filter groups */
[data-testid="stExpander"] {{ border: 1px solid {LAVENDER}2e; border-radius: 12px; background: transparent; }}
[data-testid="stExpander"] summary {{ font-weight: 600; }}

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

def movie_card(title, year, runtime, cert, rating, chips, why, watch):
    """Return the HTML for one movie card. Every result uses this one function,
    so all cards look identical and a design change happens in one place."""
    chip_html = "".join(f'<span class="cue-chip">{c}</span>' for c in chips)
    return f"""
<div class="cue-card">
<div class="cue-poster">▶</div>
<div class="cue-body">
<div class="cue-top">
<div>
<div class="cue-title">{title}</div>
<div class="cue-meta">{year} &nbsp;·&nbsp; {runtime} &nbsp;·&nbsp; {cert}</div>
</div>
<div class="cue-rating">★ {rating}</div>
</div>
<div class="cue-chips">{chip_html}</div>
<div class="cue-why">Why this pick: {why}</div>
<div class="cue-watch">{watch}</div>
</div>
</div>
"""


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
# Five filter groups, so the sidebar stays short. The vibe picker lives on the Vibe tab.
# Layout only for now: the values are stored in variables and get connected to TMDB in a later step
with st.sidebar:
    st.markdown('<div class="cue-label">Filters</div>', unsafe_allow_html=True)

    with st.expander("Genre", expanded=True):
        genres = st.multiselect("Include genres", GENRES, placeholder="Any genre")
        match_mode = st.radio("Match", ["Any of these", "All of these"], horizontal=True)
        excluded_genres = st.multiselect("Exclude genres", GENRES, placeholder="None")

    with st.expander("Release period"):
        decade = st.selectbox("Decade", DECADES)
        years = st.slider("Or pick exact years", 1920, 2026, (1990, 2026))

    with st.expander("Quality"):
        min_rating = st.slider("Minimum rating", 0.0, 10.0, 6.5, 0.5)
        min_votes = st.select_slider("Minimum votes", options=[50, 200, 500, 1000, 5000], value=200)

    with st.expander("Format"):
        runtime = st.selectbox("Runtime", RUNTIMES)
        certifications = st.multiselect("Certification", CERTIFICATIONS, placeholder="Any rating")
        language = st.selectbox("Language", list(LANGUAGES))

    with st.expander("People"):
        actor = st.text_input("Actor", placeholder="e.g. Emma Stone")
        director = st.text_input("Director", placeholder="e.g. Greta Gerwig")

# ---------- 5. WATCHED HISTORY ----------
# How long a watched movie stays out of your picks (None = never comes back)
HIDE_PERIODS = {"1 week": 7, "1 month": 30, "3 months": 90, "6 months": 180, "Forever": None}
HISTORY_COLUMNS = ["movie_id", "title", "year", "watched_on", "hidden_until"]

# The list lives in session_state, which lasts for one visit to the app.
# The History tab lets people download it and upload it again next time.
if "history" not in st.session_state:
    st.session_state["history"] = []  # one dictionary per watched movie


def mark_watched(movie_id, title, year, period):
    """Save a movie as watched and hide it for the chosen period."""
    days = HIDE_PERIODS[period]
    today = dt.date.today()
    hidden_until = "" if days is None else (today + dt.timedelta(days=days)).isoformat()
    # Drop any older entry for the same movie, then add the new one
    kept = [h for h in st.session_state["history"] if h["movie_id"] != str(movie_id)]
    kept.append({"movie_id": str(movie_id), "title": title, "year": str(year),
                 "watched_on": today.isoformat(), "hidden_until": hidden_until})
    st.session_state["history"] = kept


def bring_back(movie_id):
    """Remove a movie from the history so it can be recommended again."""
    st.session_state["history"] = [h for h in st.session_state["history"]
                                   if h["movie_id"] != str(movie_id)]


def is_hidden(movie_id):
    """True if the movie is watched and its hide period has not ended yet.
    Used to filter every list of results before it is shown."""
    today = dt.date.today().isoformat()
    for h in st.session_state["history"]:
        if h["movie_id"] == str(movie_id):
            # "" means Forever. Dates are ISO text (2026-11-10), which sort correctly.
            return h["hidden_until"] == "" or today < h["hidden_until"]
    return False


# ---------- 6. MAIN TABS ----------
(tab_mood, tab_similar, tab_compare, tab_trending,
 tab_insights, tab_search, tab_history) = st.tabs(
    ["Vibe", "Find Similar", "Compare", "Trending", "Insights", "Search", "History"]
)

# Picking a feeling pre-selects a vibe. The vibe can still be changed by hand.
def suggest_vibe():
    feeling = st.session_state.get("feeling")
    if feeling:
        st.session_state["vibe"] = FEELINGS[feeling][0]

if "vibe" not in st.session_state:
    st.session_state["vibe"] = "Uplifting"

with tab_mood:
    st.markdown('<div class="cue-label">Right now I feel</div>', unsafe_allow_html=True)
    st.pills("Right now I feel", list(FEELINGS), key="feeling", selection_mode="single",
             on_change=suggest_vibe, label_visibility="collapsed")

    st.markdown('<div class="cue-label" style="margin-top:14px;">I want to feel</div>',
                unsafe_allow_html=True)
    st.pills("I want to feel", MOODS, key="vibe", selection_mode="single",
             label_visibility="collapsed")

    # Explain the choice in one line
    feeling = st.session_state.get("feeling")
    vibe = st.session_state.get("vibe")
    if vibe:
        note = f"<b>{vibe}:</b> {MOOD_NOTES[vibe]}"
        if feeling:
            first, second = FEELINGS[feeling]
            # Only mention the suggestion while the vibe is still the one we suggested
            if vibe == first:
                note += f" &nbsp;·&nbsp; Feeling {feeling.lower()}? We started you here. Also try {second}."
        st.markdown(f'<div class="cue-note">{note}</div>', unsafe_allow_html=True)

    # SAMPLE CARD: placeholder text only, shows the layout real results will use.
    # Real results get the same two steps: skip anything is_hidden(), then show a Watched button.
    SAMPLE = {"id": 0, "title": "Sample Movie Title", "year": 2019}

    if is_hidden(SAMPLE["id"]):
        st.caption("That one is on your History list. Bring it back from the History tab.")
    else:
        st.markdown(
            movie_card(
                title=SAMPLE["title"], year=SAMPLE["year"], runtime="112 min", cert="PG-13",
                rating="7.8", chips=["Comedy", "Family", "Mood match 92%"],
                why="the plot reads warm and hopeful, and it shares genres with your mood.",
                watch="<b>Stream:</b> Netflix, Crave &nbsp;·&nbsp; <b>Rent:</b> Apple TV",
            ),
            unsafe_allow_html=True,
        )

        with st.popover("Watched it"):
            period = st.selectbox("Hide it for", list(HIDE_PERIODS), index=1, key="period_sample")
            if st.button("Save to history", type="primary", key="save_sample"):
                mark_watched(SAMPLE["id"], SAMPLE["title"], SAMPLE["year"], period)
                st.rerun()

with tab_compare:
    st.markdown('<div class="cue-label">Compare two movies</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    movie_a = col_a.text_input("First movie", placeholder="e.g. Inception")
    movie_b = col_b.text_input("Second movie", placeholder="e.g. Interstellar")
    st.button("Compare", type="primary")
    st.caption("Side-by-side ratings, runtime, box office and mood score will appear here.")

with tab_history:
    history = st.session_state["history"]
    st.markdown('<div class="cue-label">Watched</div>', unsafe_allow_html=True)

    if not history:
        st.caption("Nothing here yet. Mark a movie as watched and it will show up here.")
    else:
        hidden_now = sum(is_hidden(h["movie_id"]) for h in history)
        st.caption(f"{len(history)} watched  ·  {hidden_now} hidden from your picks right now")

        for h in sorted(history, key=lambda x: x["watched_on"], reverse=True):
            c_title, c_date, c_status, c_btn = st.columns([4, 2, 3, 2], vertical_alignment="center")
            c_title.markdown(f'<div class="cue-hist-title">{h["title"]} ({h["year"]})</div>',
                             unsafe_allow_html=True)
            c_date.markdown(f'<div class="cue-hist-meta">Watched {h["watched_on"]}</div>',
                            unsafe_allow_html=True)
            if h["hidden_until"] == "":
                status = "Hidden forever"
            elif is_hidden(h["movie_id"]):
                status = f'Hidden until {h["hidden_until"]}'
            else:
                status = "Back in your picks"
            c_status.markdown(f'<div class="cue-hist-meta">{status}</div>', unsafe_allow_html=True)
            if c_btn.button("Bring back", key=f"back_{h['movie_id']}"):
                bring_back(h["movie_id"])
                st.rerun()

    # Keep the list between visits: download it, then upload it next time
    st.markdown('<div class="cue-label" style="margin-top:28px;">Keep your list</div>',
                unsafe_allow_html=True)
    st.caption("Your list lasts for this visit. Download it to keep it, and upload it next time.")
    if history:
        csv_text = pd.DataFrame(history, columns=HISTORY_COLUMNS).to_csv(index=False)
        st.download_button("Download history", csv_text, file_name="cue-up-history.csv",
                           mime="text/csv")

    uploaded = st.file_uploader("Restore a saved history", type="csv")
    # Import each uploaded file once, otherwise it would re-import on every click
    if uploaded is not None and uploaded.file_id != st.session_state.get("imported_file"):
        imported_ok = False
        try:
            df = pd.read_csv(uploaded, dtype=str).fillna("")
            if not set(HISTORY_COLUMNS).issubset(df.columns):
                raise ValueError("missing columns")
            have = {h["movie_id"] for h in history}
            new_rows = [r for r in df[HISTORY_COLUMNS].to_dict("records")
                        if r["movie_id"] not in have]
            st.session_state["history"] = history + new_rows
            st.session_state["imported_file"] = uploaded.file_id
            imported_ok = True
        except Exception:
            st.error("That file doesn't look like a Cue Up history file. Try the one you downloaded.")
        if imported_ok:
            st.rerun()

for tab, name in [(tab_similar, "Find Similar"), (tab_trending, "Trending"),
                  (tab_insights, "Insights"), (tab_search, "Search")]:
    with tab:
        st.caption(f"{name} is being built.")

# ---------- 7. FOOTER ----------
# TMDB's terms ask for this notice wherever its data is shown
st.markdown(
    '<div class="cue-footer">Movie data from TMDB. This product uses the TMDB API but is '
    'not endorsed or certified by TMDB. Streaming availability by JustWatch.</div>',
    unsafe_allow_html=True,
)
