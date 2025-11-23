import streamlit as st
import requests
import openai
import os
import json

# --- API Configuration ---

# The key is now retrieved from Streamlit secrets (Mandatory for deployment)
try:
    openai_api_key = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API Key not found. Please set 'OPENROUTER_API_KEY' in Streamlit Secrets.")
    st.stop()


# --- Wikimedia Configuration ---
SEARCH_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    'User-Agent': 'StreamlitApp/1.0 (Contact: dreamteam@example.com)'
}

# --- Constants & Defaults ---
FORMATIONS = {
    "4-3-3": [
        ("GK", 1), ("DEF", 4), ("MID", 3), ("ATT", 3)
    ],
    "4-4-2": [
        ("GK", 1), ("DEF", 4), ("MID", 4), ("ATT", 2)
    ],
    "3-5-2": [
        ("GK", 1), ("DEF", 3), ("MID", 5), ("ATT", 2)
    ],
    "3-4-3": [
        ("GK", 1), ("DEF", 3), ("MID", 4), ("ATT", 3)
    ]
}

DEFAULT_IMAGE = "https://cdn-icons-png.flaticon.com/512/3673/3673323.png"
PITCH_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/4/4e/Football_pitch.svg"


# --- LLM Analysis Function (V1 Syntax) ---

def generate_analysis(formation, team):
    """Generates tactical analysis using the LLM (Claude-3 Haiku) using V1 syntax."""
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
        client = openai.OpenAI(
            api_key=st.secrets["OPENROUTER_API_KEY"], 
            base_url="https://openrouter.ai/api/v1",
        )
        
        with st.spinner("🧠 Analyzing tactical structure... This may take a moment."):
            response = client.chat.completions.create(
                model="anthropic/claude-3-haiku:beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=20
            )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"ERROR: LLM Analysis failed: {type(e).__name__}: {str(e)}"

# --- Dataframe for Local Players ---

def show_local_players_input():
    """
    Displays an editable Streamlit DataFrame for users to input custom player stats.
    """
    st.header("👤 Local Player Data Input")
    st.markdown("---")

    # Initialize or load existing local player data
    if 'local_players_df' not in st.session_state:
        # Define the structure for local players
        default_data = {
            'Name': ['New Player 1', 'New Player 2'],
            'Position': ['MID', 'ATT'],
            'Picture URL': [DEFAULT_IMAGE, DEFAULT_IMAGE],
            'Pace (0-100)': [85, 90],
            'Passing (0-100)': [80, 70],
            'Stamina (0-100)': [90, 80],
            'Awareness (0-100)': [85, 75],
            'Tackling (0-100)': [50, 20],
        }
        st.session_state.local_players_df = default_data

    st.info("Edit the table below to define the stats for your custom players. This data can be used in analysis later!")
    
    # Use data editor to allow user input
    edited_df = st.data_editor(
        st.session_state.local_players_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Name": st.column_config.TextColumn(required=True),
            "Position": st.column_config.SelectboxColumn(
                options=['GK', 'DEF', 'MID', 'ATT'], required=True
            ),
            "Picture URL": st.column_config.TextColumn(
                help="URL to a player image (e.g., from Wikimedia or Flaticon)",
                default=DEFAULT_IMAGE,
                required=True
            ),
            "Pace (0-100)": st.column_config.NumberColumn(min_value=0, max_value=100),
            "Passing (0-100)": st.column_config.NumberColumn(min_value=0, max_value=100),
            "Stamina (0-100)": st.column_config.NumberColumn(min_value=0, max_value=100),
            "Awareness (0-100)": st.column_config.NumberColumn(min_value=0, max_value=100),
            "Tackling (0-100)": st.column_config.NumberColumn(min_value=0, max_value=100),
        }
    )

    st.session_state.local_players_df = edited_df

    st.success(f"💾 {len(edited_df)} custom players defined.")


# --- Dynamic Positioning Logic (Existing code, unchanged) ---

@st.cache_data(ttl=3600)
def get_player_positions(formation_name):
    # ... (Your existing get_player_positions function here)
    positions = {
        "GK1": {"top": 15, "left": 50},
    }

    # Defensive Line Positions (Y = 30%)
    if formation_name in ["4-3-3", "4-4-2"]:
        positions.update({
            "DEF1": {"top": 30, "left": 15},
            "DEF2": {"top": 30, "left": 35},
            "DEF3": {"top": 30, "left": 65},
            "DEF4": {"top": 30, "left": 85},
        })
    elif formation_name in ["3-5-2", "3-4-3"]:
        positions.update({
            "DEF1": {"top": 30, "left": 25},
            "DEF2": {"top": 30, "left": 50},
            "DEF3": {"top": 30, "left": 75},
        })

    # Midfield Line Positions (Y = 50%)
    if formation_name == "4-3-3":
        positions.update({
            "MID1": {"top": 50, "left": 25},
            "MID2": {"top": 50, "left": 50},
            "MID3": {"top": 50, "left": 75},
        })
    elif formation_name == "4-4-2":
        positions.update({
            "MID1": {"top": 50, "left": 10},
            "MID2": {"top": 50, "left": 40},
            "MID3": {"top": 50, "left": 60},
            "MID4": {"top": 50, "left": 90},
        })
    elif formation_name == "3-5-2":
        positions.update({
            "MID1": {"top": 50, "left": 10},
            "MID2": {"top": 50, "left": 30},
            "MID3": {"top": 50, "left": 50},
            "MID4": {"top": 50, "left": 70},
            "MID5": {"top": 50, "left": 90},
        })
    elif formation_name == "3-4-3":
        positions.update({
            "MID1": {"top": 50, "left": 20},
            "MID2": {"top": 50, "left": 40},
            "MID3": {"top": 50, "left": 60},
            "MID4": {"top": 50, "left": 80},
        })

    # Attacking Line Positions (Y = 75%)
    if formation_name in ["4-3-3", "3-4-3"]:
        positions.update({
            "ATT1": {"top": 75, "left": 20},
            "ATT2": {"top": 75, "left": 50},
            "ATT3": {"top": 75, "left": 80},
        })
    elif formation_name in ["4-4-2", "3-5-2"]:
        positions.update({
            "ATT1": {"top": 75, "left": 40},
            "ATT2": {"top": 75, "left": 60},
        })

    return positions


# --- PITCH HTML & CSS INJECTION (Existing code, unchanged) ---

PITCH_CSS = f"""
<style>
/* ------------------------------------------- */
/* --- GLOBAL STREAMLIT CUSTOMIZATIONS --- */
/* ------------------------------------------- */

.stApp {{ background: #e8f5e9; }} 

/* Main headers (h1, h2, h3) - Targeted for BLACK text */
h1, h2, h3 {{ 
    color: #000 !important; /* Deep black for titles and section headers */
}}

/* Button Styling */
.stButton>button {{ 
    background-color: #FFD700; 
    color: #000; 
    border: 2px solid #000; 
}}
.stButton>button:hover {{ 
    background-color: #DAA520; 
    color: white; 
}}

/* ------------------------------------------- */
/* --- PITCH VISUALIZATION CSS --- */
/* ------------------------------------------- */
.pitch-container {{
    position: relative;
    width: 100%;
    aspect-ratio: 1000 / 1400; 
    background-image: url('{PITCH_IMAGE_URL}'); 
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    max-height: 800px;
}}

/* Player Marker Styling */
.player-marker {{
    position: absolute;
    width: 100px; 
    height: auto;
    text-align: center;
    transform: translate(-50%, -50%); 
    z-index: 2; 
}}

.player-marker .image-holder {{
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background-color: white; 
    border: 3px solid #FFD700; 
    margin: 0 auto;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 5px rgba(0,0,0,0.5);
}}

.player-marker img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
}}

.player-marker .name-tag {{
    background-color: white;
    color: #000; /* Player name text is black */
    font-weight: bold;
    padding: 2px 6px;
    border-radius: 4px;
    margin-top: 5px;
    white-space: nowrap;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    border: 1px solid #ccc;
    font-size: 14px;
}}

/* Style for all text within the Tactical Analysis Output container */
#analysis-content, #analysis-content h2, #analysis-content li, #analysis-content p {{
    color: #000000 !important; /* Force all analysis output text to be black */
}}
</style>
"""

# HTML template for a single player marker
PLAYER_MARKER_TEMPLATE = """
<div class="player-marker" id="slot-{key}" style="top: {top}%; left: {left}%;">
    <div class="image-holder">
        <img src="{img_url}">
    </div>
    <div class="name-tag">{name}</div>
</div>
"""

# --- Streamlit UI Layout ---

st.set_page_config(
    page_title="Dream Team Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(PITCH_CSS, unsafe_allow_html=True)
st.title("⚽ Dream Team Analyzer")

# Initialize session state variables
if 'team' not in st.session_state:
    st.session_state.team = {}
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False
# NEW: State to manage the main content view (analysis or local player input)
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'analysis' 


# --- TOP BUTTONS SECTION ---
st.markdown("---")
button_col1, button_col2 = st.columns(2)

with button_col1:
    if st.button("👥 Local Players", use_container_width=True, key="btn_local"):
        st.session_state.view_mode = 'local_players'
        # Reset analysis state when switching view
        st.session_state.run_analysis = False 
        st.rerun()

with button_col2:
    if st.button("🎬 Video Analysis", use_container_width=True, key="btn_video"):
        st.info("Initiating Video Analysis Tool... (Feature Placeholder)")
        # Switch to analysis view if the user decides to implement this later
        st.session_state.view_mode = 'analysis' 
        st.rerun()

st.markdown("---")
# ---------------------------

# --- Sidebar for Player Inputs (Existing code, unchanged) ---
with st.sidebar:
    st.header("📋 Enter Your Dream Team")
    selected_formation = st.selectbox(
        "Formation:",
        options=list(FORMATIONS.keys()),
        index=0,
        key="formation_select"
    )
    st.markdown("---")

    formation_rows = FORMATIONS[selected_formation]

    # Input fields for players
    for position_name, count in formation_rows:
        st.subheader(f"{position_name} ({count})")
        for i in range(count):
            position_key = f"{position_name}{i + 1}"

            player_name = st.text_input(
                f"Player {i + 1}:",
                key=f"input_{position_key}",
                placeholder=f"Enter {position_key} name"
            )

            st.session_state.team[position_key] = player_name

    # Analysis Button
    if st.button("🔍 Analyze Dream Team", key="analyze_button_sidebar"):
        st.session_state.run_analysis = True
        st.session_state.view_mode = 'analysis' # Ensure we switch back to analysis view
        st.rerun()
    else:
        # Only reset run_analysis if the button wasn't just clicked
        if not st.session_state.run_analysis:
            st.session_state.run_analysis = False


# --- Main Content: Pitch and Conditional Analysis/Input ---
pitch_col, analysis_col = st.columns([2, 3])

# --- Pitch Visualization (Always on the left) ---
with pitch_col:
    st.header("The Pitch")
    st.markdown(f"**Formation: {selected_formation}**")

    positions = get_player_positions(selected_formation)
    pitch_html_content = '<div class="pitch-container">'
    formation_slots = [f"{pos}{i + 1}" for pos, count in FORMATIONS[selected_formation] for i in range(count)]

    for position_key in formation_slots:
        player_name = st.session_state.team.get(position_key, "")
        display_name = player_name if player_name else position_key
        # For simplicity, still using Wikimedia fetch, but you could integrate local player pics here
        img_url = get_player_image_url(player_name) if player_name else DEFAULT_IMAGE
        pos_data = positions.get(position_key, {"top": 50, "left": 50})

        marker_html = PLAYER_MARKER_TEMPLATE.format(
            key=position_key, top=pos_data["top"], left=pos_data["left"], 
            img_url=img_url, name=display_name
        )
        pitch_html_content += marker_html

    pitch_html_content += '</div>'
    st.markdown(pitch_html_content, unsafe_allow_html=True)

# --- Analysis Output / Local Player Input (Conditional right panel) ---
with analysis_col:
    
    if st.session_state.view_mode == 'local_players':
        # New function call when 'Local Players' button is clicked
        show_local_players_input()
    
    else: # st.session_state.view_mode == 'analysis' (Default or after clicking Analyze)
        st.header("Tactical Analysis")
        if st.session_state.run_analysis:

            required_count = sum(count for _, count in formation_rows)
            filled_count = len([name for name in st.session_state.team.values() if name])

            if filled_count < required_count:
                st.error(
                    f"Please fill all {required_count} player slots. Only {filled_count} filled.")
            else:
                analysis = generate_analysis(selected_formation, st.session_state.team)
                st.markdown("---")
                
                # Use the custom styled div for the analysis output
                st.markdown(f'<div id="analysis-content">{analysis}</div>', unsafe_allow_html=True)
                
        else:
            st.info("Enter your players in the sidebar and click 'Analyze Dream Team'!")
