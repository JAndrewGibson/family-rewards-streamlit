import streamlit as st
import utils # Import shared utility functions
import time # For assignment ID generation











# --- Page Configuration ---
st.set_page_config(page_title="Rewards", page_icon="🏅", layout="wide")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("Home.py")


# --- Load Data from Session State ---
username = st.session_state.get("username")

# File paths
TASKS_TEMPLATE_FILE = 'tasks.json'
QUESTS_TEMPLATE_FILE = 'quests.json'
MISSIONS_TEMPLATE_FILE = 'missions.json'
ASSIGNED_QUESTS_FILE = 'assignments.json'

# --- Load Data (Load fresh for management/assignment actions) ---
# Use .get() from session state for config, but load templates/assignments fresh
config = st.session_state.get("config")


if not config or not username:
     st.error("User configuration not found in session state. Please log in again.")
     time.sleep(2)
     st.switch_page("Home.py")


# --- Load Existing Templates (Load fresh each time or use session state carefully) ---
task_templates = utils.load_task_templates(TASKS_TEMPLATE_FILE)
quest_templates = utils.load_quest_templates(QUESTS_TEMPLATE_FILE)
mission_templates = utils.load_mission_templates(MISSIONS_TEMPLATE_FILE)
assignments_data = utils.load_assignments(ASSIGNED_QUESTS_FILE)


current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"
st.sidebar.metric("My Points", current_points, label_visibility="visible", border=True)
st.sidebar.divider()

if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

# Handle loading errors
if task_templates is None or quest_templates is None or mission_templates is None or assignments_data is None:
    st.error("Failed to load one or more data files. Cannot proceed.")
    st.stop()
    
    
if st.session_state.get('role') == 'parent' or st.session_state.get('role') == 'admin':
    st.title("🏅 Rewards!")
    st.write("Here are all your kids rewards!")
    
if st.session_state.get('role') == 'kid' or st.session_state.get('role') == 'admin':
    st.title("🏅 Rewards!")
    st.write("Here are your rewards!")