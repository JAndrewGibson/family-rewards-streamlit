import streamlit as st
import utils # Import shared utility functions
# import time # No longer needed for sleep
import datetime # Needed for acceptance logic maybe? - Keep if used elsewhere
import auth # Assuming this handles authentication setup

# --- Page Configuration ---
st.set_page_config(page_title="Standalone Tasks", page_icon="✔️", layout="wide") # Use wide layout for better column display

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("home.py")


# --- Load Data from Session State (Ensure these are loaded reliably in home.py or login) ---
username = st.session_state.get("username")
mission_templates = st.session_state.get("mission_templates") # Keep if needed, though not directly used here
quest_templates = st.session_state.get("quest_templates")     # Keep if needed
task_templates = st.session_state.get("task_templates")
# Use 'assignments' as the consistent key for assignment data in session state
assignments_data = st.session_state.get("assignments")
points_data = st.session_state.get('points', {}) # Load points data into a variable
current_points_unformatted = points_data.get(username, 0)
current_points = f"{current_points_unformatted:,}"

# File paths needed for saving
ASSIGNMENTS_FILE = 'assignments.json'
POINTS_FILE = 'points.json' # Define points file path

# --- Robust Data Loading Checks ---
error_loading = False
missing_items = []
if not username: missing_items.append("Username")
# if mission_templates is None: missing_items.append("Mission templates") # Uncomment if needed elsewhere
# if quest_templates is None: missing_items.append("Quest templates") # Uncomment if needed elsewhere
if task_templates is None: missing_items.append("Task templates")
if assignments_data is None: missing_items.append("Assignments data")
if points_data is None: missing_items.append("Points data") # Check points too

if missing_items:
    st.error(f"❌ Critical data missing from session state: {', '.join(missing_items)}. Please try logging out and back in.")
    st.stop() # Halt execution if essential data is missing

# --- Sidebar ---
st.sidebar.metric("My Points", current_points)
if current_points_unformatted == 0:
    st.sidebar.caption("Earn points by completing tasks!")

st.sidebar.divider()

# Logout Button - Ensure 'authenticator' is loaded correctly in your main app/login flow
if 'authenticator' in st.session_state and hasattr(st.session_state['authenticator'], 'logout'):
     st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
     st.sidebar.warning("Logout functionality not available.")


# --- Parent/Admin Approval View ---
if st.session_state.get('role') in ['parent', 'admin']:
    st.title("Approve Standalone Tasks")
    config = st.session_state.get('config') # Ensure config is loaded in session state
    if not config:
        st.error("Configuration data missing. Cannot determine children.")
        st.stop()

    
    # Make sure username variable holds the PARENT'S username in this context
    parent_username = st.session_state.get("username")
    if not parent_username: # Extra check just in case
        st.error("Parent username not found in session state.")
        st.stop()
    
    
    parent_config_details = config.get('credentials',{}).get('usernames',{}).get(username,{})
    parent_children_usernames = parent_config_details.get('children', [])

    if not parent_children_usernames:
        st.info("No children assigned to this account.")
    else:
        tasks_to_approve_found = False
        for kid in parent_children_usernames:
            kid_capitalized = kid.title()
            kid_assignments = assignments_data.get(kid, {})
            kid_tasks_awaiting = {
                assign_id: assign_data for assign_id, assign_data in kid_assignments.items()
                if assign_data.get('status') == 'awaiting approval' and assign_data.get('type') == 'standalone'
            }

            if kid_tasks_awaiting:
                tasks_to_approve_found = True
                with st.expander(f"Tasks Awaiting Approval for {kid_capitalized}", expanded=True):
                    # Display in columns for better layout if many tasks
                    num_tasks = len(kid_tasks_awaiting)
                    max_cols = 3
                    num_cols = min(num_tasks, max_cols)
                    cols = st.columns(num_cols)
                    col_index = 0

                    for assign_id, assign_data in kid_tasks_awaiting.items():
                        task_id = assign_data.get('task_id') or assign_data.get('template_id')
                        task_template = task_templates.get(task_id)
                        if not task_template:
                             st.warning(f"Task template {task_id} not found for assignment {assign_id}. Skipping.")
                             continue

                        with cols[col_index % num_cols]:
                            with st.container(border=True):
                                task_name = task_template.get('name','Unnamed Task')
                                task_points = task_template.get('points', 0)
                                st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
                                st.caption(task_template.get('description', 'No description.'))
                                st.markdown(f"**Points:** {task_template.get('points', 0):,}") # Added formatting

                                # Use a unique key prefix for parent approvals
                                if st.button("✅ Approve & Award Points", key=f"approve_{kid}_{assign_id}", use_container_width=True):
                                    # 1. Get current state from session_state (which holds the full data)
                                    current_assignments_state = st.session_state["assignments"]
                                    current_points_state = st.session_state["points"]

                                    # 2. Modify state
                                    if kid in current_assignments_state and assign_id in current_assignments_state[kid]:
                                        current_assignments_state[kid][assign_id]['status'] = 'completed'
                                        task_points = task_template.get('points', 0)
                                        current_points_state[kid] = current_points_state.get(kid, 0) + task_points

                                        # 3. Save updated state to persistent storage
                                        save_assignments_ok = utils.save_assignments(current_assignments_state, ASSIGNMENTS_FILE)
                                        save_points_ok = utils.save_points(current_points_state, POINTS_FILE)

                                        if save_assignments_ok and save_points_ok:
                                            # 4. Session state already modified in step 2, no need to reassign
                                            # 5. Provide Feedback
                                            st.success(f"Task '{task_template.get('name')}' approved for {kid_capitalized}!")
                                            st.balloons()
                                            
                                            try:
                                                # Log task approval
                                                approve_msg = f"Parent '{parent_username}' approved standalone task '{task_name}' for {kid}"
                                                utils.log_into_history(
                                                    event_type="standalone_approved",
                                                    message=approve_msg,
                                                    affected_item=assign_id,
                                                    username=parent_username # Parent performed the action
                                                )

                                                # Log points awarded
                                                points_msg = f"Parent '{parent_username}' awarded {task_points} points to {kid} for completing task '{task_name}'"
                                                utils.log_into_history(
                                                    event_type="points_awarded",
                                                    message=points_msg,
                                                    affected_item=kid, # The user receiving points
                                                    username=parent_username # Parent performed the action
                                                )
                                                #Log into child history
                                                child_message = f"Your guardian '{parent_username}' approved your task '{task_name}' and awarded you {task_points} points!"
                                                utils.log_into_history(
                                                    event_type="task_completed",
                                                    message=child_message,
                                                    affected_item=task_id, # The user receiving points
                                                    username=kid # Parent performed the action
                                                )
                                            except Exception as e:
                                                st.warning(f"Could not write to history log: {e}")
                                            
                                            
                                            # 6. Trigger Rerun
                                            st.rerun()
                                        else:
                                            st.error("Failed to save changes. Please check file permissions or data integrity.")
                                            # Optionally revert changes in session state if save fails
                                            # Or just let the user retry
                                    else:
                                        st.error(f"Assignment {assign_id} for {kid_capitalized} seems to have changed or been removed. Refreshing.")
                                        st.rerun() # Rerun to show the current actual state

                                # Optional: Add a "Reject" button
                                # if st.button("❌ Reject Task", key=f"reject_{kid}_{assign_id}", use_container_width=True):
                                #    # Logic to change status to 'rejected' or back to 'active'
                                #    # Remember to save assignments and rerun

                        col_index += 1
            # else: # Optional: Show message if a specific kid has no tasks needing approval
            #     with st.expander(f"Tasks Awaiting Approval for {kid_capitalized}", expanded=False):
            #         st.info("No tasks currently awaiting approval.")

        if not tasks_to_approve_found:
             st.info("No tasks from any assigned children are currently awaiting approval.")


# --- Kid/Admin Task Management View ---
if st.session_state.get('role') in ['kid', 'admin']:
    st.title("✔️ My Standalone Tasks")
    
    # Get the current user's assignments directly from the loaded data
    # Ensure 'username' holds the KID's username in this context
    kid_username = st.session_state.get("username")
    if not kid_username: # Extra check
        st.error("User username not found in session state.")
        st.stop()

    user_assignments = assignments_data.get(username, {})

    # --- Filter tasks by status ---
    pending_assignments = {
        assign_id: data for assign_id, data in user_assignments.items()
        if data.get('status') == 'pending_acceptance' and data.get('type') == 'standalone'
    }
    active_assignments = {
        assign_id: data for assign_id, data in user_assignments.items()
        if data.get('status') == 'active' and data.get('type') == 'standalone'
    }
    assignments_awaiting_approval = {
        assign_id: data for assign_id, data in user_assignments.items()
        if data.get('status') == 'awaiting approval' and data.get('type') == 'standalone'
    }
    completed_assignments = {
        assign_id: data for assign_id, data in user_assignments.items()
        if data.get('status') == 'completed' and data.get('type') == 'standalone'
    }
    declined_assignments = {
        assign_id: data for assign_id, data in user_assignments.items()
        if data.get('status') == 'declined' and data.get('type') == 'standalone'
    }


    # --- Function to display tasks in columns ---
    def display_tasks(task_dict, section_title, empty_message, show_buttons=None):
        st.subheader(section_title)
        if not task_dict:
            st.info(empty_message)
            return

        with st.container(border=True):
            num_tasks = len(task_dict)
            max_cols = 3
            num_cols = min(num_tasks, max_cols)
            cols = st.columns(num_cols)
            col_index = 0

            for assign_id, assign_data in task_dict.items():
                task_id = assign_data.get('task_id') or assign_data.get('template_id')
                task_template = task_templates.get(task_id)
                if not task_template:
                    st.warning(f"Task template {task_id} not found for assignment {assign_id}. Skipping.")
                    continue

                with cols[col_index % num_cols]:
                    with st.container(border=True):
                        st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
                        st.caption(task_template.get('description', 'No description.'))
                        st.markdown(f"**Points:** {task_template.get('points', 0):,}") # Added formatting

                        # --- Action Buttons (Conditionally Displayed) ---
                        if show_buttons == 'accept_decline':
                            b_col1, b_col2 = st.columns(2)
                            with b_col1:
                                if st.button("✅ Accept", key=f"accept_{assign_id}", use_container_width=True):
                                    # Get state
                                    current_assignments_state = st.session_state["assignments"]
                                    # Modify state
                                    if username in current_assignments_state and assign_id in current_assignments_state[username]:
                                        current_assignments_state[username][assign_id]['status'] = 'active'
                                        # Save state
                                        if utils.save_assignments(current_assignments_state, ASSIGNMENTS_FILE):
                                            st.success(f"Task '{task_template.get('name')}' accepted!")
                                            
                                            # --- Add History Logging ---
                                            try:
                                                accept_msg = f"User '{kid_username}' accepted standalone task '{task_name}'"
                                                utils.log_into_history(
                                                    event_type="standalone_accepted",
                                                    message=accept_msg,
                                                    affected_item=assign_id,
                                                    username=kid_username # Kid performed the action
                                                )
                                            except Exception as e:
                                                st.warning(f"Could not write to history log: {e}")
                                            
                                            
                                            st.rerun()
                                        else:
                                            st.error("Failed to save acceptance.")
                                    else:
                                        st.error("Assignment not found. Refreshing.")
                                        st.rerun()

                            with b_col2:
                                if st.button("❌ Decline", key=f"decline_{assign_id}", use_container_width=True):
                                     # Get state
                                    current_assignments_state = st.session_state["assignments"]
                                    # Modify state
                                    if username in current_assignments_state and assign_id in current_assignments_state[username]:
                                        current_assignments_state[username][assign_id]['status'] = 'declined'
                                        # Save state
                                        if utils.save_assignments(current_assignments_state, ASSIGNMENTS_FILE):
                                            st.warning(f"Task '{task_template.get('name')}' declined.")
                                            
                                            # --- Add History Logging ---
                                            try:
                                                decline_msg = f"User '{kid_username}' declined standalone task '{task_name}'"
                                                utils.log_into_history(
                                                    event_type="standalone_declined",
                                                    message=decline_msg,
                                                    affected_item=assign_id,
                                                    username=kid_username # Kid performed the action
                                                )
                                            except Exception as e:
                                                st.warning(f"Could not write to history log: {e}")
                                            # --- End History Logging ---

                                            
                                            st.rerun()
                                        else:
                                            st.error("Failed to save decline.")
                                    else:
                                        st.error("Assignment not found. Refreshing.")
                                        st.rerun()


                        elif show_buttons == 'complete':
                            if st.button("🏁 Mark as Complete", key=f"complete_{assign_id}", use_container_width=True):
                                # Get state
                                current_assignments_state = st.session_state["assignments"]
                                # Modify state
                                if username in current_assignments_state and assign_id in current_assignments_state[username]:
                                    current_assignments_state[username][assign_id]['status'] = 'awaiting approval'
                                     # Save state
                                    if utils.save_assignments(current_assignments_state, ASSIGNMENTS_FILE):
                                        st.success(f"Task '{task_template.get('name')}' submitted for approval!")
                                        st.balloons()
                                        
                                        # --- Add History Logging ---
                                        try:
                                            submit_msg = f"User '{kid_username}' submitted standalone task '{task_name}' for approval"
                                            utils.log_into_history(
                                                event_type="standalone_submitted", # Changed from 'completed' to 'submitted' for clarity
                                                message=submit_msg,
                                                affected_item=assign_id,
                                                username=kid_username # Kid performed the action
                                            )
                                        except Exception as e:
                                            st.warning(f"Could not write to history log: {e}")
                                        # --- End History Logging ---
                                        
                                        st.rerun()
                                    else:
                                        st.error("Failed to submit task for approval.")
                                else:
                                    st.error("Assignment not found. Refreshing.")
                                    st.rerun()

                        elif show_buttons == 'awaiting':
                             st.info("⏳ Awaiting Parent Approval") # Indicate status clearly

                        elif show_buttons == 'completed':
                             st.success("✅ Completed!") # Indicate status clearly
                             # Optional: Add completion date if stored
                             completion_date = assign_data.get('completed_timestamp')
                             if completion_date:
                                 # You might need to parse the timestamp if it's stored as a string
                                 # Example: completed_dt = datetime.datetime.fromisoformat(completion_date)
                                 # st.caption(f"Completed on: {completed_dt.strftime('%Y-%m-%d %H:%M')}")
                                 pass # Add parsing/formatting as needed


                        elif show_buttons == 'declined':
                             st.error("❌ Declined") # Indicate status clearly
                             # Optional: Add button to re-activate or delete? Depends on desired workflow.

                col_index += 1


    # --- Display Sections using the function ---
    display_tasks(pending_assignments,
                  "🔔 Tasks Awaiting Your Acceptance",
                  "No new tasks assigned right now.",
                  show_buttons='accept_decline')

    display_tasks(active_assignments,
                  "💪 Your Active Tasks",
                  "You have no active tasks. Accept some new ones!",
                  show_buttons='complete')

    display_tasks(assignments_awaiting_approval,
                  "⏳ Tasks Awaiting Approval",
                  "No tasks are currently waiting for approval.",
                  show_buttons='awaiting') # Just show info, no button

    display_tasks(completed_assignments,
                  "🏆 Completed Tasks",
                  "You haven't completed any standalone tasks yet.",
                  show_buttons='completed') # Just show info

    # Optional: Display Declined Tasks
    # display_tasks(declined_assignments,
    #               "👎 Declined Tasks",
    #               "No tasks have been declined.",
    #               show_buttons='declined')

# --- Add some space at the bottom ---
st.markdown("---")

# Optional: Debug view for admins
# if st.session_state.get('role') == 'admin':
#     with st.expander("DEBUG: Session State"):
#         st.write(st.session_state)