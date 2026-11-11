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
RUNTIMES = ["Any length", "Under 90 min", "90 to 120
