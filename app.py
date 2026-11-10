import streamlit as st

# ---------- PAGE SETUP ----------
# Sets the browser tab title and icon, and lets the page use the full width
st.set_page_config(page_title="Cue Up", page_icon="▶", layout="wide")

# ---------- BRANDING ----------
LAVENDER = "#C5B8C8"
TEAL = "#8AA8B0"
TAGLINE = "Movie night, decided."

# Streamlit has no built-in logo option, so the wordmark is a small piece of
# HTML: a teal play symbol, "Cue" in lavender, "Up" in teal
st.markdown(
    f"""
    <h1 style="margin-bottom:0;">
        <span style="color:{TEAL};">▶</span>
        <span style="color:{LAVENDER};">Cue</span>
        <span style="color:{TEAL};">Up</span>
    </h1>
    <p style="color:#BBB2AE; margin-top:0;">{TAGLINE}</p>
    """,
    unsafe_allow_html=True,
)

st.write("Pick a mood and we'll find tonight's movie.")
