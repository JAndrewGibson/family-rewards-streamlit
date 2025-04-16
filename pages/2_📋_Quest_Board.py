# pages/1_📋_Quest_Board.py

import streamlit as st
import time
import utils # Import shared utility functions

# --- Page Configuration ---
st.set_page_config(page_title="Quest Board", page_icon="📋")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("home.py")
# --- End Authentication Check ---


# --- Load Data from Session State ---
# Check if essential data exists in session state
username = st.session_state.get("username")
quest_templates = st.session_state.get("quest_templates")
assignments_data = st.session_state.get("assignments")

# File path needed for saving
ASSIGNED_QUESTS_FILE = 'assignments.json'

if not username or quest_templates is None or assignments_data is None:
     st.error("Required data not found. Please ensure you are logged in and data files are loaded.")
     st.stop()


current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"
st.sidebar.metric("My Points", current_points)
st.sidebar.divider()

if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

# --- Page Content ---
st.title("📋 Quest Board")
st.divider()

kid_assignments = assignments_data.get(username, {})
pending_assignments = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('status') == 'pending_acceptance' and data.get('type') == 'quest' # <-- Added type check
}

if not pending_assignments:
    st.info("No new quests waiting for your approval. Great job staying up-to-date!")
else:
    st.write("Review these quests and choose to accept or decline:")
    for assign_id, assign_data in pending_assignments.items():
        quest_id = assign_data.get('quest_id') or assign_data.get('template_id') # Handle both keys
        quest_template = quest_templates.get(quest_id)

        if not quest_template:
            st.error(f"Details not found for pending quest (ID: {quest_id}).")
            continue

        with st.container(border=True):
            st.subheader(f"{quest_template.get('emoji','❓')} {quest_template.get('name','Unnamed Quest')}")
            st.caption(quest_template.get('description', 'No description.'))

            tasks_preview = quest_template.get('tasks', [])
            with st.expander("View Tasks"):
                if not tasks_preview:
                     st.write("No specific tasks listed for this quest template.")
                else:
                    for task_prev in tasks_preview:
                        st.write(f"- {task_prev.get('emoji','❓')} {task_prev.get('description','...')} ({task_prev.get('points',0)} pts)")
            st.markdown(f"**Bonus Points on Completion:** {quest_template.get('completion_bonus_points', 0)}")

            # Action Buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Accept Quest", key=f"accept_{assign_id}", use_container_width=True):
                    # Get latest data before modifying
                    current_assigned = utils.load_assignments(ASSIGNED_QUESTS_FILE) # Reload from file just in case
                    if username in current_assigned and assign_id in current_assigned[username]:
                        current_assigned[username][assign_id]['status'] = 'active'
                        if utils.save_assignments(current_assigned, ASSIGNED_QUESTS_FILE): # Check if save succeeded
                            st.session_state['assigned_quests'] = current_assigned # Update state
                            st.success(f"Quest '{quest_template.get('name')}' accepted!")
                            time.sleep(2)
                            st.rerun()
                        # Error message is handled within save_assigments
                    else:
                         st.error("Could not find assignment to accept. It might have been removed.")


            with col2:
                 if st.button("❌ Decline Quest", key=f"decline_{assign_id}", use_container_width=True):
                    # Get latest data before modifying
                    current_assigned = utils.load_assignments(ASSIGNED_QUESTS_FILE)
                    if username in current_assigned and assign_id in current_assigned[username]:
                        current_assigned[username][assign_id]['status'] = 'declined'
                        if utils.save_assignments(current_assigned, ASSIGNED_QUESTS_FILE):
                            st.session_state['assigned_quests'] = current_assigned # Update state
                            st.warning(f"Quest '{quest_template.get('name')}' declined.")
                            time.sleep(1)
                            st.rerun()
                        # Error message is handled within save_assignments
                    else:
                         st.error("Could not find assignment to decline. It might have been removed.")
        st.divider()