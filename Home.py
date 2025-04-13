# app.py (Main Entry Point for Multi-Page App)

import streamlit as st
import auth # Import the authentication module
import utils # Import the utility functions

st.set_page_config(page_title="Family Rewards", page_icon="😎")
#st.title("Home") #I don't think that this page really needs a title

# --- Configuration and Constants ---
TASKS_TEMPLATE_FILE = 'tasks.json'
QUESTS_TEMPLATE_FILE = 'quests.json'
MISSIONS_TEMPLATE_FILE = 'missions.json'
ASSIGNMENTS_FILE = 'assignments.json'
POINTS_FILE = 'points.json'

# --- Perform Authentication ---
# This handles login UI and sets 'config', 'authenticator', 'role', 'name', 'username' in session_state
name, authentication_status, username = auth.authenticate()

# --- Load Data into Session State After Login (If not already loaded) ---
if authentication_status:
    if 'quest_templates' not in st.session_state:
        st.session_state['quest_templates'] = utils.load_quest_templates(QUESTS_TEMPLATE_FILE)
    if 'assignments' not in st.session_state:
        st.session_state['assignments'] = utils.load_assignments(ASSIGNMENTS_FILE)
    if 'task_templates' not in st.session_state:
         st.session_state['task_templates'] = utils.load_task_templates(TASKS_TEMPLATE_FILE)

    if 'mission_templates' not in st.session_state:
         st.session_state['mission_templates'] = utils.load_mission_templates(MISSIONS_TEMPLATE_FILE)
    if 'points' not in st.session_state:
        st.session_state['points'] = utils.load_points(POINTS_FILE)

    if st.session_state.get('assignments') is None or \
       st.session_state.get('task_templates') is None or \
       st.session_state.get('quest_templates') is None or \
       st.session_state.get('mission_templates') is None or \
       st.session_state.get('points') is None:
         st.error("CRITICAL ERROR: Failed to load essential data files after login.")
         st.stop()

    # Ensure necessary items are in session state for pages to use
    # Most are already set by auth.authenticate()
    st.session_state['username'] = username
    st.session_state['name'] = name
    # st.session_state['role'] is set in auth.py
    # st.session_state['config'] is set in auth.py
    # st.session_state['authenticator'] is set in auth.py


# --- Main Page Content ---

st.sidebar.title("Navigation") # Add a title to the sidebar where pages appear

if authentication_status is False:
    st.error('Username/password is incorrect')
    st.info("Please enter your credentials above.")
elif authentication_status is None:
    st.warning('Please enter your username and password')
elif authentication_status is True:
    # Logged-in User Main Page
    st.title(f"Welcome, {st.session_state.get('name', 'User')}! ✨")
    st.divider()
    st.markdown("Select a page from the sidebar on the left to view your quests or manage assignments.")

    # Display basic info or summary if desired
    st.subheader("Quick Info")
    st.write(f"**Username:** {st.session_state.get('username')}")
    st.write(f"**Role:** {st.session_state.get('role', 'Unknown').capitalize()}")
    current_points = st.session_state.get('points', {}).get(username, 0)
    st.sidebar.metric("My Points ✨", current_points)
    st.sidebar.divider()

    # You could add parent-specific summaries or links here too
    if st.session_state.get('role') == 'parent':
        # Optional: Add parent-specific welcome content or navigation prompts
        st.info("Use the sidebar to assign quests to your children.")
        # Note: Parent assignment UI would need to be moved to its own page in `pages/` too.

    # Logout button in sidebar (handled within auth.authenticate's session state setup)
    if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
    else:
         st.sidebar.error("Authenticator not found.")

else: # Should not happen with current auth logic, but good practice
     st.error("Authentication status unclear. Please try logging in.")

# --- End of App ---