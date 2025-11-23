import streamlit as st
import requests
import os
from openai import OpenAI

# --- OpenAI Client Setup ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# --- Utility Functions ---
@st.cache_data(ttl=3600)
def get_player_image_url(player_name):
    """Fetch player image from Wikipedia/Wikimedia."""
    if not player_name:
        return DEFAULT_IMAGE
    try:
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{player_name} footballer",
            "format": "json"
        }
        response = requests.get(SEARCH_URL, params=search_params, headers=HEADERS)
        response.raise_for_status()
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
            "pithumbsize": 200,
            "pilicense": "any"
        }
        image_response = requests.get(SEARCH_URL, params=image_params, headers=HEADERS)
        image_response.raise_for_status()
        image_data = image_response.json()
        pages = image_data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]
        return DEFAULT_IMAGE
    except Exception:
        return DEFAULT_IMAGE

def generate_analysis(formation, team):
    """Generates tactical analysis using OpenAI 1.x Chat API."""
    team_str = "\n".join([f"{pos}: {name}" for pos, name in team.items()])

    prompt = f"""You are a professional football analyst and scout.
Analyze this team's tactical profile based on the {formation} formation.
Team Roster:
{team_str}

Provide your analysis in the following strict Markdown structure. Do not include any text before the first heading:

## Strengths 💪
* [Sharp point about a key advantage]
* ...

## Weaknesses 🚧
* [Sharp point about a potential liability]
* ...

## Tactical Suggestions 🧠
* [Concrete suggestion for the coach]
* ...
"""

    try:
        with st.spinner("🧠 Analyzing tactical structure... This may take a moment."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use a model available to your API key
                messages=[
                    {"role": "system", "content": "You are a professional football analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6
            )

        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: LLM Analysis failed: {str(e)}"

# --- Player Positioning ---
def get_player_positions(formation_name):
    positions = {"GK1": {"top": 15, "left": 50}}
    if formation_name in ["4-3-3", "4-4-2"]:
        positions.update({
            "DEF1": {"top": 30, "left": 15}, "DEF2": {"top": 30, "left": 35},
            "DEF3": {"top": 30, "left": 65}, "DEF4": {"top": 30, "left": 85},
        })
    elif formation_name in ["3-5-2", "3-4-3"]:
        positions.update({
            "DEF1": {"top": 30, "left": 25}, "DEF2": {"top": 30, "left": 50}, "DEF3": {"top": 30, "left": 75},
        })
    if formation_name == "4-3-3":
        positions.update({"MID1": {"top": 50, "left": 25}, "MID2": {"top": 50, "left": 50}, "MID3": {"top": 50, "left": 75}})
    elif formation_name == "4-4-2":
        positions.update({"MID1": {"top": 50, "left": 10}, "MID2": {"top": 50, "left": 40}, "MID3": {"top": 50, "left": 60}, "MID4": {"top": 50, "left": 90}})
    elif formation_name == "3-5-2":
        positions.update({"MID1": {"top": 50, "left": 10}, "MID2": {"top": 50, "left": 30}, "MID3": {"top": 50, "left": 50}, "MID4": {"top": 50, "left": 70}, "MID5": {"top": 50, "left": 90}})
    elif formation_name == "3-4-3":
        positions.update({"MID1": {"top": 50, "left": 20}, "MID2": {"top": 50, "left": 40}, "MID3": {"top": 50, "left": 60}, "MID4": {"top": 50, "left": 80}})
    if formation_name in ["4-3-3", "3-4-3"]:
        positions.update({"ATT1": {"top": 75, "left": 20}, "ATT2": {"top": 75, "left": 50}, "ATT3": {"top": 75, "left": 80}})
    elif formation_name in ["4-4-2", "3-5-2"]:
        positions.update({"ATT1": {"top": 75, "left": 40}, "ATT2": {"top": 75, "left": 60}})
    return positions

# --- CSS & HTML ---
PITCH_CSS = f"""
<style>
.stApp {{ background: #e8f5e9; }}
h1, h2, h3 {{ color: #000 !important; }}
.stButton>button {{ background-color: #FFD700; color: #000; border: 2px solid #000; }}
.stButton>button:hover {{ background-color: #DAA520; color: white; }}
.pitch-container {{ position: relative; width: 100%; aspect-ratio: 1000/1400; background-image: url('{PITCH_IMAGE_URL}'); background-size: contain; background-repeat: no-repeat; background-position: center; max-height: 800px; }}
.player-marker {{ position: absolute; width: 100px; text-align: center; transform: translate(-50%, -50%); z-index: 2; }}
.player-marker .image-holder {{ width: 50px; height: 50px; border-radius: 50%; background-color: white; border: 3px solid #FFD700; margin: 0 auto; overflow: hidden; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 5px rgba(0,0,0,0.5); }}
.player-marker img {{ width: 100%; height: 100%; object-fit: cover; }}
.player-marker .name-tag {{ background-color: white; color: #000; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-top: 5px; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.3); border: 1px solid #ccc; font-size: 14px; }}
</style>
"""

PLAYER_MARKER_TEMPLATE = """
<div class="player-marker" style="top: {top}%; left: {left}%;>
    <div class="image-holder">
        <img src="{img_url}">
    </div>
    <div class="name-tag">{name}</div>
</div>
"""

# --- Streamlit UI ---
st.set_page_config(page_title="Dream Team Analyzer", layout="wide")
st.markdown(PITCH_CSS, unsafe_allow_html=True)
st.title("⚽ Dream Team Analyzer")

if 'team' not in st.session_state:
    st.session_state.team = {}
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False

# Sidebar
with st.sidebar:
    st.header("📋 Enter Your Dream Team")
    selected_formation = st.selectbox("Formation:", options=list(FORMATIONS.keys()), index=0)
    st.markdown("---")

    formation_rows = FORMATIONS[selected_formation]
    for position_name, count in formation_rows:
        st.subheader(f"{position_name} ({count})")
        for i in range(count):
            position_key = f"{position_name}{i+1}"
            player_name = st.text_input(f"Player {i+1}:", key=f"input_{position_key}", placeholder=f"Enter {position_key} name")
            st.session_state.team[position_key] = player_name

    if st.button("🔍 Analyze Dream Team"):
        st.session_state.run_analysis = True
    else:
        st.session_state.run_analysis = False

# Main content
pitch_col, analysis_col = st.columns([2, 3])

with pitch_col:
    st.header("The Pitch")
    st.markdown(f"**Formation: {selected_formation}**")
    positions = get_player_positions(selected_formation)
    pitch_html = '<div class="pitch-container">'
    formation_slots = [f"{pos}{i+1}" for pos, count in FORMATIONS[selected_formation] for i in range(count)]
    for position_key in formation_slots:
        player_name = st.session_state.team.get(position_key, "")
        display_name = player_name if player_name else position_key
        img_url = get_player_image_url(player_name) if player_name else DEFAULT_IMAGE
        pos_data = positions.get(position_key, {"top":50, "left":50})
        pitch_html += PLAYER_MARKER_TEMPLATE.format(top=pos_data["top"], left=pos_data["left"], img_url=img_url, name=display_name)
    pitch_html += "</div>"
    st.markdown(pitch_html, unsafe_allow_html=True)

with analysis_col:
    st.header("Tactical Analysis")
    if st.session_state.run_analysis:
        required_count = sum(count for _, count in formation_rows)
        filled_count = len([name for name in st.session_state.team.values() if name])
        if filled_count < required_count:
            st.error(f"Please fill all {required_count} player slots. Only {filled_count} filled.")
        else:
            analysis = generate_analysis(selected_formation, st.session_state.team)
            st.markdown("---")
            st.markdown(analysis)
    else:
        st.info("Enter your players in the sidebar and click 'Analyze Dream Team'!")
