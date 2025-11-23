import streamlit as st
import requests
import os
import json
from openrouter import OpenRouter  # ✅ OFFICIAL SDK

# --- API CONFIGURATION (OpenRouter + Claude Haiku) ---

client = OpenRouter(api_key=st.secrets["OPENROUTER_API_KEY"])   # ✅ Correct way


# --- Wikimedia Configuration ---
SEARCH_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    'User-Agent': 'StreamlitApp/1.0 (Contact: dreamteam@example.com)'
}

# --- Constants & Defaults ---
FORMATIONS = {
    "4-3-3": [("GK", 1), ("DEF", 4), ("MID", 3), ("ATT", 3)],
    "4-4-2": [("GK", 1), ("DEF", 4), ("MID", 4), ("ATT", 2)],
    "3-5-2": [("GK", 1), ("DEF", 3), ("MID", 5), ("ATT", 2)],
    "3-4-3": [("GK", 1), ("DEF", 3), ("MID", 4), ("ATT", 3)]
}

DEFAULT_IMAGE = "https://cdn-icons-png.flaticon.com/512/3673/3673323.png"
PITCH_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/4/4e/Football_pitch.svg"



# --- IMAGE FETCHING --------------------------------------

@st.cache_data(ttl=3600)
def get_player_image_url(player_name):
    if not player_name:
        return DEFAULT_IMAGE

    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{player_name} footballer",
        "format": "json"
    }

    try:
        response = requests.get(SEARCH_URL, params=search_params, headers=HEADERS)
        data = response.json()

        results = data.get("query", {}).get("search", [])
        if not results:
            return DEFAULT_IMAGE

        page_title = results[0]["title"]

        image_params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "pageimages",
            "pithumbsize": 300
        }

        img_res = requests.get(SEARCH_URL, params=image_params, headers=HEADERS)
        pages = img_res.json().get("query", {}).get("pages", {})

        for page in pages.values():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]

        return DEFAULT_IMAGE

    except:
        return DEFAULT_IMAGE




# --- LLM ANALYSIS (OpenRouter) -----------------------------

def generate_analysis(formation, team):
    team_text = "\n".join([f"{pos}: {name}" for pos, name in team.items()])

    prompt = f"""
You are a professional football analyst.
Analyze the squad in formation {formation}.

Team:
{team_text}

Provide Markdown with these sections:

## Strengths
- ...

## Weaknesses
- ...

## Tactical Suggestions
- ...
"""

    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )

        return response.choices[0].message["content"]

    except Exception as e:
        return f"ERROR: {e}"



# --- FORMATION POSITIONING --------------------------------

def get_player_positions(formation):
    positions = {"GK1": {"top": 15, "left": 50}}

    if formation in ["4-3-3", "4-4-2"]:
        positions.update({
            "DEF1": {"top": 30, "left": 15},
            "DEF2": {"top": 30, "left": 35},
            "DEF3": {"top": 30, "left": 65},
            "DEF4": {"top": 30, "left": 85},
        })
    elif formation in ["3-5-2", "3-4-3"]:
        positions.update({
            "DEF1": {"top": 30, "left": 25},
            "DEF2": {"top": 30, "left": 50},
            "DEF3": {"top": 30, "left": 75},
        })

    if formation == "4-3-3":
        positions.update({
            "MID1": {"top": 50, "left": 25},
            "MID2": {"top": 50, "left": 50},
            "MID3": {"top": 50, "left": 75}
        })
    elif formation == "4-4-2":
        positions.update({
            "MID1": {"top": 50, "left": 10},
            "MID2": {"top": 50, "left": 40},
            "MID3": {"top": 50, "left": 60},
            "MID4": {"top": 50, "left": 90}
        })
    elif formation == "3-5-2":
        positions.update({
            "MID1": {"top": 50, "left": 10},
            "MID2": {"top": 50, "left": 30},
            "MID3": {"top": 50, "left": 50},
            "MID4": {"top": 50, "left": 70},
            "MID5": {"top": 50, "left": 90},
        })
    elif formation == "3-4-3":
        positions.update({
            "MID1": {"top": 50, "left": 20},
            "MID2": {"top": 50, "left": 40},
            "MID3": {"top": 50, "left": 60},
            "MID4": {"top": 50, "left": 80},
        })

    if formation in ["4-3-3", "3-4-3"]:
        positions.update({
            "ATT1": {"top": 75, "left": 20},
            "ATT2": {"top": 75, "left": 50},
            "ATT3": {"top": 75, "left": 80},
        })
    elif formation in ["4-4-2", "3-5-2"]:
        positions.update({
            "ATT1": {"top": 75, "left": 40},
            "ATT2": {"top": 75, "left": 60},
        })

    return positions




# --- STREAMLIT UI ------------------------------------------

st.set_page_config(page_title="Dream Team Analyzer", layout="wide")
st.title("⚽ Dream Team Analyzer")

if "team" not in st.session_state:
    st.session_state.team = {}

with st.sidebar:
    st.header("Team Input")

    formation = st.selectbox("Formation", FORMATIONS.keys())
    st.markdown("---")

    for pos, count in FORMATIONS[formation]:
        st.subheader(f"{pos} ({count})")
        for i in range(count):
            key = f"{pos}{i+1}"
            st.session_state.team[key] = st.text_input(key)

    if st.button("Analyze"):
        st.session_state.run = True

col1, col2 = st.columns([2, 3])

# --- Pitch Drawing -----------------------------------------

with col1:
    st.header("Pitch")

    pos_map = get_player_positions(formation)

    pitch_html = '<div style="position:relative;width:100%;aspect-ratio:1000/1400;background-size:contain;background-image:url(\'%s\');">' % PITCH_IMAGE_URL

    for key, name in st.session_state.team.items():
        top = pos_map.get(key, {}).get("top", 50)
        left = pos_map.get(key, {}).get("left", 50)
        img = get_player_image_url(name) if name else DEFAULT_IMAGE

        pitch_html += f"""
        <div style="position:absolute;top:{top}%;left:{left}%;transform:translate(-50%,-50%);text-align:center;">
            <img src="{img}" width="60" style="border-radius:50%;border:3px solid gold;">
            <div style="background:#fff;padding:3px 6px;border-radius:4px;border:1px solid #ccc;">
                {name or key}
            </div>
        </div>
        """

    pitch_html += "</div>"
    st.markdown(pitch_html, unsafe_allow_html=True)

# --- LLM Output --------------------------------------------

with col2:
    st.header("Analysis")

    if st.session_state.get("run"):
        analysis = generate_analysis(formation, st.session_state.team)
        st.markdown(analysis)
    else:
        st.info("Fill the squad and click Analyze.")
