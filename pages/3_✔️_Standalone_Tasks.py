import streamlit as st
import utils # Import shared utility functions
import time
import datetime # Needed for acceptance logic maybe?
import auth

# --- Page Configuration ---
st.set_page_config(page_title="Standalone Tasks", page_icon="✔️")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("home.py")
    

# --- Load Data from Session State ---
username = st.session_state.get("username")
mission_templates = st.session_state.get("mission_templates")
quest_templates = st.session_state.get("quest_templates")
task_templates = st.session_state.get("task_templates")
assignments_data = st.session_state.get("assignments")
current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"

# File path needed for saving
ASSIGNMENTS_FILE = 'assignments.json'

# Check if all necessary data is loaded (Using more verbose checks from previous step)
error_loading = False
if not username: st.error("❌ Username not found."); error_loading = True
if mission_templates is None: st.error("❌ Mission templates missing."); error_loading = True
if quest_templates is None: st.error("❌ Quest templates missing."); error_loading = True
if task_templates is None: st.error("❌ Task templates missing."); error_loading = True
if assignments_data is None: st.error("❌ Assignments data missing."); error_loading = True
if error_loading: st.stop()

if current_points == 0:
    st.sidebar.write('''No points yet! Don't worry, as soon as you earn some points - they'll appear here!
                     ''')
else:
    st.sidebar.metric("My Points", current_points)
    
st.sidebar.divider()

if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

# --- Page Content ---
st.title("✔️ Standalone Tasks")
st.divider()

kid_assignments = assignments_data.get(username, {})
pending_assignments = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('status') == 'pending_acceptance' and data.get('type') == 'standalone'
}

if not pending_assignments:
    st.info("No tasks assigned at this time")
else:
    st.write("Review these tasks and choose to accept or decline:")
    for assign_id, assign_data in pending_assignments.items():
        task_id = assign_data.get('task_id') or assign_data.get('template_id') # Handle both keys
        task_template = task_templates.get(task_id)

        if not task_template:
            st.error(f"Details not found for pending task (ID: {task_id}).")
            continue

        with st.container(border=True):
            st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
            st.caption(task_template.get('description', 'No description.'))

            tasks_preview = task_template.get('tasks', [])
            with st.expander("View Tasks"):
                if not tasks_preview:
                     st.write("No specific tasks listed for this quest template.")
                else:
                    for task_prev in tasks_preview:
                        st.write(f"- {task_prev.get('emoji','❓')} {task_prev.get('description','...')} ({task_prev.get('points',0)} pts)")
            st.markdown(f"**Points:** {task_template.get('completion_bonus_points', 0)}")

            # Action Buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Accept task", key=f"accept_{assign_id}", use_container_width=True):
                    # Get latest data before modifying
                    current_assigned = utils.load_assignments(ASSIGNMENTS_FILE) # Reload from file just in case
                    if username in current_assigned and assign_id in current_assigned[username]:
                        current_assigned[username][assign_id]['status'] = 'active'
                        if utils.save_assignments(current_assigned, ASSIGNMENTS_FILE): # Check if save succeeded
                            st.session_state['assigned_tasks'] = current_assigned # Update state
                            st.success(f"Task '{task_template.get('name')}' accepted!")
                            time.sleep(2)
                            st.rerun()
                        # Error message is handled within save_assigments
                    else:
                         st.error("Could not find assignment to accept. It might have been removed.")


            with col2:
                 if st.button("❌ Decline Task", key=f"decline_{assign_id}", use_container_width=True):
                    # Get latest data before modifying
                    current_assigned = utils.load_assignments(ASSIGNMENTS_FILE)
                    if username in current_assigned and assign_id in current_assigned[username]:
                        current_assigned[username][assign_id]['status'] = 'declined'
                        if utils.save_assignments(current_assigned, ASSIGNMENTS_FILE):
                            st.session_state['assigned_tasks'] = current_assigned # Update state
                            st.warning(f"Task '{task_template.get('name')}' declined.")
                            time.sleep(1)
                            st.rerun()
                        # Error message is handled within save_assignments
                    else:
                         st.error("Could not find assignment to decline. It might have been removed.")
        st.divider()