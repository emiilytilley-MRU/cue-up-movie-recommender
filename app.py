import base64
import datetime as dt
import html
import re

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# =====================================================================
# CUE UP  |  Movie night, decided.
# Section 1: page setup      Section 2: design system (colours + CSS)
# Section 3: header          Section 4: sidebar filters
# Section 5: watched history Section 6: TMDB data (movie details, cards)
# Section 7: recommender engine (mood + content matching)
# Section 8: main tabs       Section 9: footer
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

# Choices for the sidebar filters
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

# TMDB's numbers for each genre (these are fixed by TMDB)
GENRE_IDS = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35, "Crime": 80,
    "Documentary": 99, "Drama": 18, "Family": 10751, "Fantasy": 14, "History": 36,
    "Horror": 27, "Music": 10402, "Mystery": 9648, "Romance": 10749,
    "Science Fiction": 878, "Thriller": 53, "War": 10752, "Western": 37,
}
# Runtime choice -> (shortest, longest) in minutes. None means no limit.
RUNTIME_BOUNDS = {
    "Any length": (None, None), "Under 90 min": (None, 89),
    "90 to 120 min": (90, 120), "Over 120 min": (121, None),
}
# Each vibe = genres it looks in + the plot tone it wants (VADER score, -1 to +1)
# "all": True means a movie needs every listed genre; False means any one of them.
# These tone ranges are starting points. The Insights tab shows how real plots are spread.
MOOD_RULES = {
    "Uplifting":     {"genres": [35, 10751, 10402], "all": False, "tone": (0.3, 1.0)},
    "Light & funny": {"genres": [35, 16],           "all": False, "tone": (0.0, 1.0)},
    "Romantic":      {"genres": [10749],            "all": False, "tone": (0.1, 1.0)},
    "Bittersweet":   {"genres": [10749, 18],        "all": True,  "tone": (-1.0, 0.1)},
    "Thoughtful":    {"genres": [18, 99],           "all": False, "tone": (-0.3, 0.3)},
    "Adventurous":   {"genres": [12, 14, 878, 28],  "all": False, "tone": (-1.0, 1.0)},
    "Tense":         {"genres": [53, 9648],         "all": False, "tone": (-1.0, -0.3)},
    "Dark & heavy":  {"genres": [80, 10752, 27],    "all": False, "tone": (-1.0, -0.5)},
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
.cue-poster img {{ width: 100%; height: 100%; object-fit: cover; border-radius: 10px; }}
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

/* Compare and Search tables */
.cue-table {{ width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 0.92rem; }}
.cue-table th {{ text-align: left; color: {LAVENDER}; font-weight: 700; padding: 10px 12px;
                 border-bottom: 1px solid {LAVENDER}44; }}
.cue-table td {{ padding: 9px 12px; color: {SOFT_WHITE}; border-bottom: 1px solid {TAUPE}22; vertical-align: top; }}
.cue-table td.cue-rowlabel {{ color: {TAUPE}; font-size: 0.82rem; font-weight: 600; width: 22%; }}
.cue-table td.win {{ color: {TEAL}; font-weight: 700; }}
.cue-small {{ max-width: 460px; }}

.cue-footer {{ color: {TAUPE}; font-size: 0.78rem; text-align: center; opacity: 0.8;
               border-top: 1px solid {TAUPE}33; padding-top: 16px; margin-top: 40px; }}
</style>
""",
    unsafe_allow_html=True,
)

def movie_card(title, year, runtime, cert, rating, chips, why, watch, poster=None):
    """Return the HTML for one movie card. Every result uses this one function,
    so all cards look identical and a design change happens in one place.
    Text from TMDB is escaped so a title like "Tom & Jerry" cannot break the layout."""
    chip_html = "".join(f'<span class="cue-chip">{html.escape(str(c))}</span>' for c in chips)
    poster_html = f'<img src="{poster}" alt="">' if poster else "▶"
    return f"""
<div class="cue-card">
<div class="cue-poster">{poster_html}</div>
<div class="cue-body">
<div class="cue-top">
<div>
<div class="cue-title">{html.escape(str(title))}</div>
<div class="cue-meta">{year} &nbsp;·&nbsp; {runtime} &nbsp;·&nbsp; {html.escape(str(cert))}</div>
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
# Five filter groups, so the sidebar stays short. The vibe picker lives on the Vibe tab. Layout only for now:
# the values are stored in variables and get connected to TMDB in a later step
with st.sidebar:
    st.markdown('<div class="cue-label">Filters</div>', unsafe_allow_html=True)

    with st.expander("Genre", expanded=True):
        genres = st.multiselect("Include genres", GENRES, placeholder="Any genre")
        match_mode = st.radio("Match", ["Any of these", "All of these"], horizontal=True)
        excluded_genres = st.multiselect("Exclude genres", GENRES, placeholder="None")

    with st.expander("Release period"):
        decade = st.selectbox("Decade", DECADES, help="A decade overrides the year slider.")
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


def watched_control(movie_id, title, year, scope):
    """The 'Watched it' button under a card. It opens a small box where you
    choose how long to hide the movie. scope (the tab name) keeps the boxes of the
    same movie in different tabs separate."""
    with st.popover("Watched it"):
        period = st.selectbox("Hide it for", list(HIDE_PERIODS), index=1, key=f"period_{scope}_{movie_id}")
        if st.button("Save to history", type="primary", key=f"save_{scope}_{movie_id}"):
            mark_watched(movie_id, title, year, period)
            st.rerun()


# ---------- 6. TMDB DATA ----------
TMDB_BASE = "https://api.themoviedb.org/3"       # every TMDB address starts with this
TMDB_IMG = "https://image.tmdb.org/t/p/w342"     # posters are served from here
# One extra request bundles everything a card needs, instead of five separate ones
DETAIL_PARTS = "credits,keywords,release_dates,watch/providers"


@st.cache_data(ttl=3600, show_spinner=False)
def tmdb_get(path, **params):
    """Ask TMDB for something and return the reply as a Python dictionary.
    The key comes from Streamlit's secrets, so it is never written in this file.
    Replies are remembered for an hour (cached), which keeps the app fast and
    stays well under TMDB's request limits."""
    key = st.secrets["TMDB_API_KEY"]
    reply = requests.get(f"{TMDB_BASE}{path}", params={"api_key": key, **params}, timeout=10)
    reply.raise_for_status()  # turns a failed request into an error we can catch
    return reply.json()


def safe_tmdb(path, **params):
    """Same as tmdb_get, but a problem becomes a friendly message instead of a crash.
    Returns None when something went wrong."""
    try:
        return tmdb_get(path, **params)
    except (KeyError, FileNotFoundError):
        st.error("The TMDB key is missing. Add TMDB_API_KEY to your app's secrets.")
    except requests.HTTPError as err:
        if err.response is not None and err.response.status_code == 401:
            st.error("TMDB rejected the key. Check that it is the short v3 API key.")
        else:
            st.error("TMDB returned an error. Wait a minute and try again.")
    except requests.RequestException:
        st.error("Could not reach TMDB. Check your connection and try again.")
    return None


def certification(m):
    """Age rating such as PG or R. US first (it matches the filter), then Canada."""
    entries = m.get("release_dates", {}).get("results", [])
    for country in ("US", "CA"):
        for entry in entries:
            if entry.get("iso_3166_1") == country:
                for release in entry.get("release_dates", []):
                    if release.get("certification"):
                        return release["certification"]
    return "N/A"


def watch_text(m, country="CA"):
    """One line saying where to stream, rent or buy the movie in Canada."""
    options = m.get("watch/providers", {}).get("results", {}).get(country, {})
    parts = []
    for label, kind in (("Stream", "flatrate"), ("Rent", "rent"), ("Buy", "buy")):
        names = [p["provider_name"] for p in options.get(kind, [])][:3]
        if names:
            parts.append(f"<b>{label}:</b> {html.escape(', '.join(names))}")
    return " &nbsp;·&nbsp; ".join(parts) if parts else "Not listed for Canada"


def show_movie(m, why, scope, extra_chips=()):
    """Turn one TMDB movie record into a card, with the Watched button under it.
    scope is the tab name. It keeps each tab's buttons separate when the same
    movie shows up in two tabs. Missing data (no poster, no runtime) shows as N/A."""
    title = m.get("title") or "Untitled"
    year = (m.get("release_date") or "")[:4] or "N/A"
    runtime = f"{m['runtime']} min" if m.get("runtime") else "N/A"
    poster = f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None
    rating = f"{m['vote_average']:.1f}" if m.get("vote_count") else "NR"
    genre_chips = [g["name"] for g in m.get("genres", [])][:3]
    st.markdown(
        movie_card(title=title, year=year, runtime=runtime, cert=certification(m),
                   rating=rating, chips=list(extra_chips) + genre_chips, why=why,
                   watch=watch_text(m), poster=poster),
        unsafe_allow_html=True,
    )
    watched_control(m["id"], title, year, scope)


def show_picks(ranked, why_for, chips_for, scope, state_key, per_page=6):
    """Show the top movies from a ranked list as cards, skipping watched ones.
    why_for(m) and chips_for(m) build the explanation and the extra chips.
    A 'Show more' button adds another page of cards."""
    visible = [m for m in ranked if not is_hidden(m["id"])]
    if not visible:
        st.caption("Nothing to show. Try loosening a filter, or bring a movie back from History.")
        return
    count = st.session_state.get(state_key, per_page)
    for m in visible[:count]:
        detail = safe_tmdb(f"/movie/{m['id']}", append_to_response=DETAIL_PARTS)
        if detail is None:  # the error message is already on screen, so stop here
            return
        show_movie(detail, why_for(m), scope, chips_for(m))
    if len(visible) > count and st.button(f"Show {per_page} more", key=f"more_{scope}"):
        st.session_state[state_key] = count + per_page
        st.rerun()


# ---------- 7. RECOMMENDER ENGINE ----------
# Two approaches live here:
#   1. Mood (sentiment): VADER scores how positive or negative a plot summary reads.
#   2. Content (TF-IDF): compares plot words and genres between movies.
# Find Similar blends both into a hybrid score.
GENRE_BY_ID = {v: k for k, v in GENRE_IDS.items()}


@st.cache_resource(show_spinner=False)
def get_vader():
    return SentimentIntensityAnalyzer()


def tone(text):
    """VADER score for a plot summary: -1 (very negative) to +1 (very positive)."""
    return get_vader().polarity_scores(text or "")["compound"]


def tone_words(score):
    if score >= 0.5:
        return "warm and upbeat"
    if score >= 0.2:
        return "mostly hopeful"
    if score > -0.2:
        return "balanced, neither bright nor bleak"
    if score > -0.5:
        return "fairly serious"
    return "dark and intense"


def mood_fit(score, mood):
    """1.0 inside the mood's tone range, falling to 0 when 0.6 or more outside it."""
    low, high = MOOD_RULES[mood]["tone"]
    gap = max(low - score, score - high, 0)
    return max(0.0, 1 - gap / 0.6)


def best_mood(score, moods):
    """Of the chosen moods, the one this tone fits best, with its fit (0 to 1)."""
    return max(((mood, mood_fit(score, mood)) for mood in moods), key=lambda pair: pair[1])


def mood_genre_ok(m, mood):
    """Does the movie carry the genres this mood asks for?"""
    rule = MOOD_RULES[mood]
    have, need = set(m.get("genre_ids", [])), set(rule["genres"])
    return need <= have if rule["all"] else bool(need & have)


# The sidebar choices, gathered in one dictionary so every tab can use them
filters = {
    "genres": genres, "match_all": match_mode == "All of these", "exclude": excluded_genres,
    "decade": decade, "years": years, "min_rating": min_rating, "min_votes": min_votes,
    "run_min": RUNTIME_BOUNDS[runtime][0], "run_max": RUNTIME_BOUNDS[runtime][1],
    "certs": certifications, "language": LANGUAGES[language],
    "actor": actor.strip(), "director": director.strip(),
}


def date_range(f):
    """First and last release date as text. A chosen decade overrides the year slider.
    The end is capped at today so unreleased films never appear."""
    if f["decade"] != "Any":
        start = int(f["decade"][:4])
        low, high = start, start + 9
    else:
        low, high = f["years"]
    last = min(dt.date(high, 12, 31), dt.date.today())
    return f"{low}-01-01", last.isoformat()


def find_person(name):
    """TMDB's id for an actor or director name, or None if there is no match."""
    if not name:
        return None
    data = safe_tmdb("/search/person", query=name)
    results = (data or {}).get("results", [])
    if data is not None and not results:
        st.warning(f'Could not find "{name}" on TMDB, so that filter was skipped.')
    return results[0]["id"] if results else None


def build_params(f, mood=None):
    """Turn the filter choices into the parameters TMDB's /discover/movie expects."""
    params = {"sort_by": "popularity.desc", "include_adult": "false",
              "vote_average.gte": f["min_rating"], "vote_count.gte": f["min_votes"]}
    params["primary_release_date.gte"], params["primary_release_date.lte"] = date_range(f)

    # Genres: a comma means AND, a pipe means OR. Your genre picks win over the mood's.
    if f["genres"]:
        params["with_genres"] = ("," if f["match_all"] else "|").join(str(GENRE_IDS[g]) for g in f["genres"])
    elif mood:
        rule = MOOD_RULES[mood]
        params["with_genres"] = ("," if rule["all"] else "|").join(map(str, rule["genres"]))
    if f["exclude"]:
        params["without_genres"] = "|".join(str(GENRE_IDS[g]) for g in f["exclude"])

    if f["run_min"] is not None:
        params["with_runtime.gte"] = f["run_min"]
    if f["run_max"] is not None:
        params["with_runtime.lte"] = f["run_max"]
    if f["certs"]:
        params["certification_country"] = "US"
        params["certification"] = "|".join(f["certs"])
    if f["language"]:
        params["with_original_language"] = f["language"]

    actor_id, director_id = find_person(f["actor"]), find_person(f["director"])
    if actor_id:
        params["with_cast"] = actor_id
    if director_id:
        params["with_crew"] = director_id
    return params


def collect(params, pages=3):
    """Gather up to 20 movies per page from /discover/movie into one list."""
    movies, seen = [], set()
    for page in range(1, pages + 1):
        data = safe_tmdb("/discover/movie", page=page, **params)
        if data is None:
            break
        for m in data.get("results", []):
            if m["id"] not in seen:
                seen.add(m["id"])
                movies.append(m)
        if page >= data.get("total_pages", 1):
            break
    return movies


def passes_basic(m, f):
    """Re-check a movie against the filters we can test from list data alone.
    Used for lists TMDB did not filter for us, and as a safety net on the rest."""
    gids = set(m.get("genre_ids", []))
    if f["exclude"] and gids & {GENRE_IDS[g] for g in f["exclude"]}:
        return False
    if f["genres"]:
        want = {GENRE_IDS[g] for g in f["genres"]}
        if not (want <= gids if f["match_all"] else want & gids):
            return False
    if (m.get("vote_average") or 0) < f["min_rating"] or (m.get("vote_count") or 0) < f["min_votes"]:
        return False
    low, high = date_range(f)
    released = m.get("release_date") or ""
    if not released or not (low <= released <= high):
        return False
    if f["language"] and m.get("original_language") != f["language"]:
        return False
    return True


def vibe_rank(pool, mood, f):
    """Rank candidates for a mood. Score = 70% mood fit (plot tone) + 30% TMDB rating."""
    rows = []
    for m in pool:
        if not m.get("overview") or not mood_genre_ok(m, mood) or not passes_basic(m, f):
            continue
        t = tone(m["overview"])
        fit = mood_fit(t, mood)
        rows.append({**m, "_tone": t, "_fit": fit,
                     "_score": 0.7 * fit + 0.3 * (m.get("vote_average") or 0) / 10})
    return sorted(rows, key=lambda r: -r["_score"])


def vibe_rank_many(pools, moods, f):
    """Rank movies for several moods at once. A movie counts if it fits any chosen mood;
    it keeps its best score and remembers which mood it matched."""
    best = {}
    for mood in moods:
        for row in vibe_rank(pools[mood], mood, f):
            row["_mood"] = mood
            if row["id"] not in best or row["_score"] > best[row["id"]]["_score"]:
                best[row["id"]] = row
    return sorted(best.values(), key=lambda r: -r["_score"])


def active_filter_names(f):
    """Plain names of the filters in use, for the 'no results' message."""
    names = []
    if f["genres"] or f["exclude"]: names.append("genres")
    if f["decade"] != "Any" or tuple(f["years"]) != (1990, 2026): names.append("release period")
    if f["min_rating"] > 6.5 or f["min_votes"] > 200: names.append("quality")
    if f["run_min"] is not None or f["run_max"] is not None: names.append("runtime")
    if f["certs"]: names.append("certification")
    if f["language"]: names.append("language")
    if f["actor"] or f["director"]: names.append("people")
    return names


# ----- Find Similar: content-based matching (TF-IDF) with an optional mood blend -----
def doc_text(overview, genre_names, keywords=()):
    """One block of text per movie: plot, theme keywords, and genre tags.
    Genre names are joined into single tokens (ScienceFiction) and repeated so they carry weight."""
    tags = " ".join(g.replace(" ", "") for g in genre_names)
    return f"{overview or ''} {' '.join(keywords)} {tags} {tags}"


def similarity_rank(base_text, base_genres, pool, moods, weight):
    """Score every candidate against the movie you picked.
    content = TF-IDF cosine similarity, scaled so the closest candidate is 1.0.
    With vibes chosen: match = (1 - weight) * content + weight * mood fit (the hybrid).
    With several vibes, the best-fitting one counts."""
    texts = [base_text]
    names_for = []
    for m in pool:
        names = [GENRE_BY_ID[g] for g in m.get("genre_ids", []) if g in GENRE_BY_ID]
        names_for.append(names)
        texts.append(doc_text(m.get("overview"), names))
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    scores = cosine_similarity(matrix[0], matrix[1:])[0]
    top = max(scores.max(), 1e-9)
    features = vectorizer.get_feature_names_out()
    genre_tokens = {g.replace(" ", "").lower() for g in GENRES}

    rows = []
    for i, m in enumerate(pool):
        content = scores[i] / top
        t = tone(m["overview"])
        mood, fit = best_mood(t, moods) if moods else (None, 0.0)
        match = (1 - weight) * content + weight * fit if moods else content
        # Why: shared genres, plus the words that pull the two plots together
        shared = [g for g in names_for[i] if g in base_genres]
        overlap = matrix[0].multiply(matrix[i + 1]).toarray()[0]
        words = [features[j] for j in overlap.argsort()[::-1][:6]
                 if overlap[j] > 0 and features[j] not in genre_tokens][:3]
        parts = []
        if shared:
            parts.append("shares the genres " + ", ".join(shared[:3]))
        if words:
            parts.append("has plot words in common: " + ", ".join(words))
        why = "it " + " and ".join(parts) + "." if parts else "its plot reads like the movie you picked."
        if mood:
            why += f" Plot tone is {tone_words(t)}, a {round(fit * 100)}% fit for {mood.lower()}."
        rows.append({**m, "_match": match, "_why": why})
    return sorted(rows, key=lambda r: -r["_match"])


# ----- Compare: two movies side by side -----
def load_for_compare(title):
    """Find a movie by title and load its full details. Shows a message if nothing is found."""
    found = safe_tmdb("/search/movie", query=title)
    results = (found or {}).get("results", [])
    if found is not None and not results:
        st.caption(f'No movie called "{title}" found. Check the spelling.')
        return None
    if not results:
        return None
    return safe_tmdb(f"/movie/{results[0]['id']}", append_to_response=DETAIL_PARTS)


def money(value):
    return f"${value:,.0f}" if value else "N/A"  # TMDB uses 0 when it does not know


def compare_table(a, b):
    """A side-by-side HTML table. The better value in a row is highlighted."""
    def director(m):
        crew = m.get("credits", {}).get("crew", [])
        return ", ".join(c["name"] for c in crew if c.get("job") == "Director")[:60] or "N/A"

    def cast(m):
        return ", ".join(c["name"] for c in m.get("credits", {}).get("cast", [])[:3]) or "N/A"

    def row(label, va, vb, better=None):
        """better = 'high' highlights the larger number. va/vb are (number, text)."""
        ca = cb = ""
        if better == "high" and va[0] and vb[0] and va[0] != vb[0]:
            ca, cb = ("win", "") if va[0] > vb[0] else ("", "win")
        return (f'<tr><td class="cue-rowlabel">{label}</td>'
                f'<td class="{ca}">{html.escape(str(va[1]))}</td><td class="{cb}">{html.escape(str(vb[1]))}</td></tr>')

    def plain(text):
        return (None, text)

    def facts(m):
        return {
            "year": (m.get("release_date") or "")[:4] or "N/A",
            "runtime": f"{m['runtime']} min" if m.get("runtime") else "N/A",
            "rating": ((m.get("vote_average") or 0) if m.get("vote_count") else 0,
                       f"★ {m['vote_average']:.1f} ({m['vote_count']:,} votes)" if m.get("vote_count") else "NR"),
            "budget": (m.get("budget") or 0, money(m.get("budget"))),
            "revenue": (m.get("revenue") or 0, money(m.get("revenue"))),
            "genres": ", ".join(g["name"] for g in m.get("genres", [])) or "N/A",
            "tone": (tone(m.get("overview")), f"{tone(m.get('overview')):+.2f}, {tone_words(tone(m.get('overview')))}"),
        }

    fa, fb = facts(a), facts(b)
    watch = lambda m: re.sub(r"<[^>]+>", "", watch_text(m)).replace("&nbsp;", " ")
    rows = [
        row("Released", plain(fa["year"]), plain(fb["year"])),
        row("Runtime", plain(fa["runtime"]), plain(fb["runtime"])),
        row("Age rating", plain(certification(a)), plain(certification(b))),
        row("TMDB rating", fa["rating"], fb["rating"], "high"),
        row("Budget", fa["budget"], fb["budget"]),
        row("Box office", fa["revenue"], fb["revenue"], "high"),
        row("Genres", plain(fa["genres"]), plain(fb["genres"])),
        row("Director", plain(director(a)), plain(director(b))),
        row("Top cast", plain(cast(a)), plain(cast(b))),
        row("Plot tone", fa["tone"], fb["tone"]),
        row("Where to watch (CA)", plain(watch(a)), plain(watch(b))),
    ]
    title = lambda m: html.escape(f"{m.get('title', 'Untitled')}")
    return (f'<table class="cue-table"><tr><th></th><th>{title(a)}</th><th>{title(b)}</th></tr>'
            + "".join(rows) + "</table>")


# ----- Insights: charts -----
def style_chart(fig):
    """Same look for every chart: transparent background, palette colours."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=SOFT_WHITE, family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=50, b=10), height=340,
        xaxis=dict(gridcolor="rgba(187,178,174,0.15)", zeroline=False),
        yaxis=dict(gridcolor="rgba(187,178,174,0.15)", zeroline=False),
    )
    return fig


def tone_histogram(df, moods):
    fig = go.Figure(go.Histogram(x=df["tone"], xbins=dict(start=-1, end=1, size=0.1),
                                 marker=dict(color=TEAL, line=dict(color=SLATE, width=1))))
    for mood in moods:
        low, high = MOOD_RULES[mood]["tone"]
        fig.add_vrect(x0=max(low, -1), x1=min(high, 1), fillcolor=LAVENDER, opacity=0.18,
                      line_width=0, annotation_text=mood, annotation_font_color=SOFT_WHITE)
    fig.update_layout(title="Plot tone scores (how many movies at each score)",
                      xaxis_title="Tone score", yaxis_title="Movies")
    return style_chart(fig)


def tone_scatter(df):
    fig = go.Figure(go.Scatter(x=df["tone"], y=df["rating"], mode="markers", hovertext=df["title"],
                               marker=dict(color=LAVENDER, size=9, line=dict(color=PLUM, width=1))))
    fig.update_layout(title="Does a brighter plot mean a higher rating?",
                      xaxis_title="Tone score", yaxis_title="TMDB rating")
    return style_chart(fig)


# ----- Search: plain-English parser (rules, no AI model) -----
GENRE_WORDS = {
    "comedy": "Comedy", "comedies": "Comedy", "funny": "Comedy", "action": "Action",
    "adventure": "Adventure", "animated": "Animation", "animation": "Animation",
    "cartoon": "Animation", "crime": "Crime", "documentary": "Documentary",
    "documentaries": "Documentary", "drama": "Drama", "dramas": "Drama", "family": "Family",
    "fantasy": "Fantasy", "history": "History", "historical": "History", "horror": "Horror",
    "scary": "Horror", "music": "Music", "musical": "Music", "mystery": "Mystery",
    "romance": "Romance", "romantic": "Romance", "sci-fi": "Science Fiction",
    "scifi": "Science Fiction", "science fiction": "Science Fiction", "thriller": "Thriller",
    "thrillers": "Thriller", "war": "War", "western": "Western", "westerns": "Western",
}
STOP = r"(?=\s+(?:and|from|under|over|rated|in|directed|starring|featuring|before|after|since|that|but|not|no)\b|[,.;]|$)"


def parse_query(text):
    """Turn a sentence into the same filter dictionary the sidebar makes.
    Returns (filters, notes). notes is a list of (label, value) pairs shown back to the user."""
    t = " " + text.lower().strip() + " "
    f = {"genres": [], "match_all": True, "exclude": [], "decade": "Any",
         "years": (1920, dt.date.today().year), "min_rating": 6.0, "min_votes": 100,
         "run_min": None, "run_max": None, "certs": [], "language": None, "actor": "", "director": ""}
    notes = []
    words = sorted(GENRE_WORDS, key=len, reverse=True)  # longest first, so "science fiction" beats "science"

    # People first, so their names are not read as genre words
    m = re.search(r"(?:directed by|director)\s+([a-z.'\- ]+?)" + STOP, t)
    if m:
        f["director"] = m.group(1).strip().title()
        t = t.replace(m.group(0), " ")
        notes.append(("Director", f["director"]))
    m = re.search(r"(?:starring|featuring|with)\s+([a-z.'\- ]+?)" + STOP, t)
    if m:
        f["actor"] = m.group(1).strip().title()
        t = t.replace(m.group(0), " ")
        notes.append(("Actor", f["actor"]))

    # Exclusions: "not horror", "no war", "without romance"
    for w in words:
        hit = re.search(r"\b(?:not|no|without|except)\s+" + re.escape(w) + r"\b", t)
        if hit:
            if GENRE_WORDS[w] not in f["exclude"]:
                f["exclude"].append(GENRE_WORDS[w])
            t = t.replace(hit.group(0), " ")
    if f["exclude"]:
        notes.append(("Exclude", ", ".join(f["exclude"])))

    # Genres: "and" (the default) means all of them, "or" means any of them
    for w in words:
        if (re.search(r"\b" + re.escape(w) + r"\b", t) and GENRE_WORDS[w] not in f["genres"]
                and GENRE_WORDS[w] not in f["exclude"]):  # "not horror" beats "scary"
            f["genres"].append(GENRE_WORDS[w])
    if f["genres"]:
        f["match_all"] = " or " not in t
        notes.append(("Genres", (" or " if not f["match_all"] else " + ").join(f["genres"])))

    # Decade: "90s", "1990s", "2000s"
    m = re.search(r"\b(19|20)?(\d)0s\b", t)
    if m:
        digit = int(m.group(2))
        start = int((m.group(1) or ("20" if digit < 3 else "19")) + m.group(2) + "0")
        f["years"] = (start, start + 9)
        notes.append(("Years", f"{start} to {start + 9}"))
    low = re.search(r"\b(?:after|since|from)\s+((?:19|20)\d\d)\b", t)
    high = re.search(r"\b(?:before|until|up to)\s+((?:19|20)\d\d)\b", t)
    if low or high:
        f["years"] = (int(low.group(1)) if low else 1920, int(high.group(1)) if high else dt.date.today().year)
        notes.append(("Years", f"{f['years'][0]} to {f['years'][1]}"))

    # Runtime: "under 100 minutes", "over 2 hours"
    for m in re.finditer(r"\b(under|less than|shorter than|below|over|longer than|more than)\s+(\d+(?:\.\d+)?)\s*"
                         r"(hours?|hrs?|h|minutes?|mins?)\b", t):
        minutes = round(float(m.group(2)) * (60 if m.group(3).startswith("h") else 1))
        if m.group(1) in ("under", "less than", "shorter than", "below"):
            f["run_max"] = minutes
            notes.append(("Runtime", f"under {minutes} min"))
        else:
            f["run_min"] = minutes
            notes.append(("Runtime", f"over {minutes} min"))

    # Age rating: "rated R", or PG / PG-13 / NC-17 on their own
    certs = re.findall(r"\brated\s+(pg-13|pg|nc-17|g|r)\b", t) + re.findall(r"\b(pg-13|nc-17)\b", t)
    if not certs and re.search(r"\bpg\b", t):
        certs = ["pg"]
    f["certs"] = sorted({c.upper() for c in certs})
    if f["certs"]:
        notes.append(("Rated", ", ".join(f["certs"])))

    # Language: "in French", "Korean movies"
    for name, code in LANGUAGES.items():
        if code and re.search(r"\bin\s+" + name.lower() + r"\b|\b" + name.lower() + r"[- ](?:language|movies?|films?|dramas?)\b", t):
            f["language"] = code
            notes.append(("Language", name))
            break

    # Quality
    if re.search(r"\b(best|top|highly rated|acclaimed|great)\b", t):
        f["min_rating"], f["min_votes"] = 7.5, 500
        notes.append(("Rating", "7.5 or higher"))
    return f, notes


def notes_table(notes):
    """Show what the parser understood, so the search never feels like a black box."""
    rows = "".join(f'<tr><td class="cue-rowlabel">{html.escape(k)}</td><td>{html.escape(str(v))}</td></tr>'
                   for k, v in notes)
    return f'<table class="cue-table cue-small"><tr><th colspan="2">What I understood</th></tr>{rows}</table>'


# ---------- 8. MAIN TABS ----------
(tab_mood, tab_similar, tab_compare, tab_trending,
 tab_insights, tab_search, tab_history) = st.tabs(
    ["Vibe", "Find Similar", "Compare", "Trending", "Insights", "Search", "History"]
)


# Picking a feeling pre-selects a vibe. The vibe can still be changed by hand.
def suggest_vibe():
    chosen = st.session_state.get("feeling") or []
    if chosen:
        picks = []
        for feeling in chosen:
            if FEELINGS[feeling][0] not in picks:
                picks.append(FEELINGS[feeling][0])
        st.session_state["vibe"] = picks


if "vibe" not in st.session_state:
    st.session_state["vibe"] = ["Uplifting"]

with tab_mood:
    st.markdown('<div class="cue-label">Right now I feel (pick any)</div>', unsafe_allow_html=True)
    st.pills("Right now I feel", list(FEELINGS), key="feeling", selection_mode="multi",
             on_change=suggest_vibe, label_visibility="collapsed")

    st.markdown('<div class="cue-label" style="margin-top:14px;">I want to feel (pick any)</div>',
                unsafe_allow_html=True)
    st.pills("I want to feel", MOODS, key="vibe", selection_mode="multi",
             label_visibility="collapsed")

    vibes = list(st.session_state.get("vibe") or [])
    if not vibes:
        st.caption("Pick at least one vibe above to see movies.")
    else:
        notes = " &nbsp;·&nbsp; ".join(f"<b>{v}:</b> {MOOD_NOTES[v]}" for v in vibes)
        st.markdown(f'<div class="cue-note">{notes}</div>', unsafe_allow_html=True)

        with st.spinner("Finding movies for your vibes..."):
            pools = {v: collect(build_params(filters, v)) for v in vibes}
            ranked = vibe_rank_many(pools, vibes, filters)
        total = len({m["id"] for p in pools.values() for m in p})
        if total and not ranked:
            st.caption("Candidates were found, but none fit these vibes with your filters. "
                       "Try a different vibe or loosen a filter.")
        elif not total:
            used = active_filter_names(filters)
            st.caption("No movies matched. Filters in use: " + (", ".join(used) or "none")
                       + ". Loosen one and try again.")
        else:
            st.caption(f"{len(ranked)} movies fit, from {total} candidates. Best fit first.")
            show_picks(
                ranked,
                why_for=lambda m: (f"the plot reads {tone_words(m['_tone'])} "
                                   f"(tone {m['_tone']:+.2f}), which fits {m['_mood'].lower()}."),
                chips_for=lambda m: [f"{m['_mood']} {round(m['_fit'] * 100)}%"],
                scope="vibe", state_key="n_vibe_" + "_".join(vibes),
            )

# Find Similar: content-based (TF-IDF) with an optional mood blend (hybrid)
with tab_similar:
    st.markdown('<div class="cue-label">Find movies like one you love</div>', unsafe_allow_html=True)
    liked = st.text_input("Movie you like", placeholder="e.g. Inception", key="liked_title")
    blend_moods = st.multiselect("Blend in vibes (optional)", MOODS, key="blend_mood",
                                 placeholder="No vibe")
    weight = 0.3
    if blend_moods:
        weight = st.slider("How much the vibe counts", 0, 100, 30, 10, format="%d%%") / 100
    st.caption("Your sidebar filters for genre, release period, quality and language apply here. "
               "Runtime, certification and people filters apply to Vibe and Search.")

    if liked.strip():
        found = safe_tmdb("/search/movie", query=liked.strip())
        options = (found or {}).get("results", [])[:5]
        if found is not None and not options:
            st.caption(f'No movie called "{liked}" found. Check the spelling.')
        elif options:
            labels = [f"{o.get('title', 'Untitled')} ({(o.get('release_date') or 'N/A')[:4]})" for o in options]
            pick = st.selectbox("Which one?", range(len(options)), format_func=lambda i: labels[i],
                                key="liked_pick") if len(options) > 1 else 0
            base = safe_tmdb(f"/movie/{options[pick]['id']}", append_to_response="keywords")
            if base is not None:
                base_genres = [g["name"] for g in base.get("genres", [])]
                base_words = [k["name"] for k in base.get("keywords", {}).get("keywords", [])]
                base_text = doc_text(base.get("overview"), base_genres, base_words)
                with st.spinner("Comparing plots..."):
                    top_ids = [str(g["id"]) for g in base.get("genres", [])][:2]
                    candidates = []
                    for path in (f"/movie/{base['id']}/recommendations", f"/movie/{base['id']}/similar"):
                        data = safe_tmdb(path)
                        candidates += (data or {}).get("results", [])
                    if top_ids:
                        candidates += collect({"with_genres": ",".join(top_ids), "sort_by": "popularity.desc",
                                               "vote_count.gte": 200}, pages=1)
                    seen, pool = {base["id"]}, []
                    for m in candidates:
                        if m["id"] not in seen and m.get("overview") and passes_basic(m, filters):
                            seen.add(m["id"])
                            pool.append(m)
                if not pool:
                    st.caption("No similar movies passed your filters. Loosen a filter and try again.")
                else:
                    ranked = similarity_rank(base_text, base_genres, pool,
                                             blend_moods, weight)
                    st.caption(f"Movies like {base.get('title')}, from {len(pool)} candidates. Best match first.")
                    show_picks(
                        ranked,
                        why_for=lambda m: m["_why"],
                        chips_for=lambda m: [f"Match {round(m['_match'] * 100)}%"],
                        scope="similar", state_key=f"n_sim_{base['id']}_{'_'.join(blend_moods)}",
                    )

# Compare: two movies side by side
with tab_compare:
    st.markdown('<div class="cue-label">Compare two movies</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    name_a = col_a.text_input("First movie", placeholder="e.g. Inception")
    name_b = col_b.text_input("Second movie", placeholder="e.g. Interstellar")
    if name_a.strip() and name_b.strip():
        pair = [load_for_compare(name_a.strip()), load_for_compare(name_b.strip())]
        if all(pair):
            st.markdown(compare_table(*pair), unsafe_allow_html=True)
            winner = max(pair, key=lambda m: m.get("vote_average") or 0)
            if (pair[0].get("vote_average") or 0) != (pair[1].get("vote_average") or 0):
                st.caption(f"Higher TMDB rating: {winner.get('title')} "
                           f"({winner.get('vote_average', 0):.1f}).")
    else:
        st.caption("Enter two titles to see ratings, runtime, box office and plot tone side by side.")

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


with tab_trending:
    st.markdown('<div class="cue-label">Trending this week</div>', unsafe_allow_html=True)
    with st.spinner("Loading this week's trending movies..."):
        trending = safe_tmdb("/trending/movie/week")
        items = (trending or {}).get("results", [])
        if trending is not None and not items:
            st.caption("Nothing is trending right now. Try again later.")
        if items:
            show_picks(items, why_for=lambda m: "it is one of the most-watched films on TMDB this week.",
                       chips_for=lambda m: [], scope="trending", state_key="n_trending")

# Insights: how plot tone is spread across the movies your filters allow
with tab_insights:
    st.markdown('<div class="cue-label">How plot tone is spread</div>', unsafe_allow_html=True)
    st.caption("Each movie's plot summary gets a tone score from -1 (very negative) to +1 (very positive). "
               "This is the score the Vibe tab uses. Your sidebar filters apply.")
    pool = [m for m in collect(build_params(filters)) if m.get("overview")]
    if len(pool) < 3:
        st.caption("Not enough movies under these filters to chart. Loosen a filter.")
    else:
        chart_df = pd.DataFrame({
            "title": [m.get("title", "Untitled") for m in pool],
            "tone": [tone(m["overview"]) for m in pool],
            "rating": [m.get("vote_average") or 0 for m in pool],
        })
        s1, s2, s3 = st.columns(3)
        s1.metric("Movies analysed", len(chart_df))
        s2.metric("Average tone", f"{chart_df['tone'].mean():+.2f}")
        s3.metric("Positive plots", f"{(chart_df['tone'] > 0.05).mean() * 100:.0f}%")
        shade = st.multiselect("Highlight vibe tone ranges", MOODS, key="insight_mood", placeholder="None")
        st.plotly_chart(tone_histogram(chart_df, shade), width="stretch")
        st.plotly_chart(tone_scatter(chart_df), width="stretch")

# Search: plain-English search, parsed by rules (no AI model involved)
with tab_search:
    st.markdown('<div class="cue-label">Search in plain English</div>', unsafe_allow_html=True)
    query = st.text_input("What are you looking for?", key="search_text",
                          placeholder="e.g. funny family movies from the 90s under 100 minutes")
    st.caption("Understands genres, decades or years, runtime, ratings like PG, languages, "
               "\"starring\" and \"directed by\", and \"not horror\". Your sidebar filters are ignored here.")
    if query.strip():
        parsed, notes = parse_query(query)
        if not notes:
            st.caption("No filters recognised. Try: \"scary movies from the 80s\" or \"French dramas rated R\".")
        else:
            st.markdown(notes_table(notes), unsafe_allow_html=True)
        with st.spinner("Searching..."):
            pool = [m for m in collect(build_params(parsed), pages=2) if passes_basic(m, parsed)]
        if not pool:
            st.caption("No movies matched. Loosen something in your search.")
        else:
            summary = "; ".join(f"{k.lower()} {v}" for k, v in notes) or "your search"
            show_picks(pool, why_for=lambda m: f"it matches {summary}.", chips_for=lambda m: [],
                       scope="search", state_key=f"n_search_{query.strip().lower()}")


# ---------- 9. FOOTER ----------
# TMDB's terms ask for this notice wherever its data is shown
st.markdown(
    '<div class="cue-footer">Movie data from TMDB. This product uses the TMDB API but is '
    'not endorsed or certified by TMDB. Streaming availability by JustWatch.</div>',
    unsafe_allow_html=True,
)
