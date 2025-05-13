import streamlit as st
import utils # Import shared utility functions
import time

# --- Page Configuration ---
st.set_page_config(page_title="Missions", page_icon="🗺️", layout="wide")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("Home.py")
    

# --- Load Data from Session State ---
username = st.session_state.get("username")
mission_templates = st.session_state.get("mission_templates")
quest_templates = st.session_state.get("quest_templates")
task_templates = st.session_state.get("task_templates")
assignments_data = st.session_state.get("assignments")
current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"

# File paths
ASSIGNMENTS_FILE = 'assignments.json'

# Error checking
error_loading = False
if not username: st.error("❌ Username not found."); error_loading = True
if mission_templates is None: st.error("❌ Mission templates missing."); error_loading = True
if quest_templates is None: st.error("❌ Quest templates missing."); error_loading = True
if task_templates is None: st.error("❌ Task templates missing."); error_loading = True
if assignments_data is None: st.error("❌ Assignments data missing."); error_loading = True
if error_loading: st.stop()

st.sidebar.metric("My Points", current_points, label_visibility="visible", border=True)    
st.sidebar.divider()

if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

# --- Page Content ---
st.title("🗺️ Your Missions")
st.divider()

kid_assignments = assignments_data.get(username, {})

# --- 1. Pending Acceptance Section ---
pending_missions = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'mission' and data.get('status') == 'pending_acceptance'
}

if not pending_missions:
    pass

else:
    st.header("📬 Incoming Missions")
    # Outer loop: Correctly iterates through each PENDING mission assignment
    for assign_id, mission_assignment_data in pending_missions.items():
        mission_template_id = mission_assignment_data.get('template_id')
        mission_template = mission_templates.get(mission_template_id)

        if not mission_template:
            st.error(f"Details not found for pending mission template (ID: {mission_template_id}). Assignment ID: {assign_id}")
            continue

        # --- Calculate Total Points for THIS mission ---
        # Start with the base mission completion points
        total_points = mission_template.get('mission_combined_points', '')
        contained_quests = mission_template.get('contains_quests', [])
        contained_tasks = mission_template.get('contains_tasks', [])


        # --- Display Container for the Mission ---
        with st.container(border=True):
            st.subheader(f"{mission_template.get('emoji','🗺️')} {mission_template.get('name','Unnamed Mission')}")
            st.caption(mission_template.get('description', 'No description.'))

            # Display the calculated total points clearly
            st.markdown(f"**Total Potential Points:** {total_points} points.")

            # --- Expander for Mission Components ---
            # Use a unique key for the expander based on the assignment ID if needed,
            # though often not strictly necessary for expanders unless controlling state.
            with st.expander("View Mission Components"):
                # Use columns for better layout
                quest_column, task_column = st.columns(2)

                with quest_column:
                    st.markdown("**Quests:**")
                    if not contained_quests:
                        st.caption("No quests in this mission.")
                    else:
                        for quest_id in contained_quests:
                            quest_info = quest_templates.get(quest_id)
                            if quest_info:
                                quest_points = quest_info.get('completion_bonus_points', 0)
                                st.markdown(f"**{quest_info.get('name', 'Unnamed Quest')}** ({quest_points} pts)")
                                st.caption(f"{quest_info.get('description', '')}")

                                # --- MODIFIED SECTION FOR TASKS WITHIN QUEST ---
                                tasks_in_quest = quest_info.get('tasks', []) # Get the list associated with the 'tasks' key
                                if tasks_in_quest:
                                    st.markdown("*Tasks within quest:*")
                                    # Iterate assuming each item IS the task detail dictionary
                                    for task_detail in tasks_in_quest:
                                        # Check if the item is actually a dictionary before trying to get keys
                                        if isinstance(task_detail, dict):
                                            task_name = task_detail.get('name', 'Unnamed Task')
                                            task_points = task_detail.get('points', 0)
                                            task_desc = task_detail.get('description', '')
                                            # Display the details directly from task_detail
                                            st.markdown(f"- {task_name} ({task_points} pts)")
                                            st.caption(f"  - {task_desc}")
                                        else:
                                            # Output a warning if the format isn't the expected dictionary
                                            st.warning(f"  - Unexpected task format found within quest: {task_detail}")
                                else:
                                    st.caption("  - No specific tasks listed for this quest.")
                                # --- END MODIFIED SECTION ---

                            else:
                                st.warning(f"Quest ID {quest_id} not found. Tell Andrew! :)")

                with task_column:
                    st.markdown("**Standalone Tasks:**")
                    if not contained_tasks:
                        st.caption("No standalone tasks in this mission.")
                    else:
                        for task_id in contained_tasks:
                            task_info = task_templates.get(task_id)
                            if task_info:
                                st.markdown(f"**{task_info.get('name', 'Unnamed Task')}** ({task_info.get('points', 0)} pts)")
                                st.caption(f"{task_info.get('description', '')}")
                            else:
                                st.warning(f"Task ID {task_id} not found.")

                # Display base mission reward again for clarity if desired
                st.divider()
                st.markdown(f"**Mission Completion Reward:**")
                st.markdown(f"- Points: {mission_template.get('completion_reward', {}).get('points', 0)}")
                other_reward = mission_template.get('completion_reward',{}).get('description')
                if other_reward:
                    st.markdown(f"- Other: {other_reward}")

            # --- Action Buttons (Your existing logic seems correct here) ---
            # Keys are correctly unique using assign_id
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Accept Mission", key=f"accept_m_{assign_id}", use_container_width=True):
                    # --- Your existing acceptance logic ---
                    current_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                    if username in current_assignments and assign_id in current_assignments[username]:
                         current_assignments[username][assign_id]['status'] = 'accepted'
                         current_assignments[username][assign_id].setdefault('quest_instances', {})
                         current_assignments[username][assign_id].setdefault('task_instances', {})
                         if utils.save_assignments(current_assignments, ASSIGNMENTS_FILE):
                             st.session_state['assignments'] = current_assignments
                             st.success(f"Mission '{mission_template.get('name')}' accepted!")
                             time.sleep(1)
                             st.rerun()
                    else:
                        st.error("Could not find mission assignment to accept.")
                    # --- End Acceptance Logic ---

            with col2:
                if st.button("❌ Decline Mission", key=f"decline_m_{assign_id}", use_container_width=True):
                    # --- Your existing decline logic ---
                    current_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                    if username in current_assignments and assign_id in current_assignments[username]:
                        current_assignments[username][assign_id]['status'] = 'declined'
                        if utils.save_assignments(current_assignments, ASSIGNMENTS_FILE):
                            st.session_state['assignments'] = current_assignments
                            st.warning(f"Mission '{mission_template.get('name')}' declined.")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("Could not find mission assignment to decline.")
                    # --- End Decline Logic ---

        st.divider() # Separate each pending mission visually

# --- 2. Accepted Missions Section ---

accepted_missions = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'mission' and data.get('status') == 'accepted'
}

if not accepted_missions:
    pass
else:
    st.header("🎯 Accepted Missions")
    st.write(f"Click on a mission to see its components ({len(accepted_missions)}):")
    # Removed the top-level divider, will rely on spacing around expanders

    for assign_id, mission_assignment_data in accepted_missions.items():
        mission_template_id = mission_assignment_data.get('template_id')
        mission_template = mission_templates.get(mission_template_id)

        if not mission_template:
            st.error(f"Could not find template details for Mission ID {mission_template_id}. Skipping.")
            continue # Skip this iteration if template is missing

        # --- Use Expander for each Accepted Mission ---
        # Create a descriptive label for the expander
        expander_label = f"{mission_template.get('emoji','🗺️')} {mission_template.get('name','Unnamed Mission')}"
        # You could add a high-level status here too if you calculate it
        #expander_label += " (In Progress)" # Example

        with st.expander(expander_label, expanded=False): # Start collapsed

            # Display Mission Description inside Expander
            st.caption(mission_template.get('description', 'No description available.'))
            # TODO: Add overall mission progress bar/summary here?

            st.markdown("---") # Divider inside expander, above components

            # --- Get Components ---
            contained_quests = mission_template.get('contains_quests', [])
            contained_tasks = mission_template.get('contains_tasks', []) # Standalone tasks

            # --- Handle Case with No Components ---
            if not contained_quests and not contained_tasks:
                st.info("This mission has no defined components in its template.")
            else:
                # --- Create Columns INSIDE the Expander ---
                # Adjust column ratios if needed, e.g., [2, 1] for wider quest column
                col_quests, col_tasks = st.columns(2)

                # --- Column 1: Quests and their nested Tasks ---
                with col_quests:
                    st.markdown("**Quests**")
                    if not contained_quests:
                        st.caption("No quests defined.")
                    else:
                        for quest_id in contained_quests:
                            quest_template = quest_templates.get(quest_id)
                            if quest_template:
                                # --- Display Quest Status ---
                                current_status = utils.calculate_item_status(
                                    quest_id, 'quest', mission_template, mission_assignment_data
                                )
                                status_icon = "🔒" if current_status == "locked" else "✅" if current_status == "completed" else "▶️"
                                quest_name = quest_template.get('name', 'Unknown Quest')
                                quest_emoji = quest_template.get('emoji','⚔️')

                                # Display quest line (removed explicit status text for brevity)
                                if current_status == "completed":
                                    st.markdown(f"- {status_icon} ~~{quest_emoji} {quest_name}~~")
                                elif current_status == "locked":
                                    st.markdown(f"- {status_icon} {quest_emoji} {quest_name}")
                                else: # Active
                                    st.markdown(f"- {status_icon} {quest_emoji} **{quest_name}**")

                                # --- Display Tasks WITHIN this Quest (indented look) ---
                                tasks_in_quest = quest_template.get('tasks', [])
                                if tasks_in_quest:
                                    for task_detail in tasks_in_quest:
                                        if isinstance(task_detail, dict):
                                            task_name = task_detail.get('name', 'Unnamed Task')
                                            task_points = task_detail.get('points', 0)
                                            task_desc = task_detail.get('description', '') # Keep if needed
                                            task_emoji_nested = task_detail.get('emoji', '🔸')
                                            # Use Markdown non-breaking spaces for visual indent
                                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{task_emoji_nested} {task_name} ({task_points} pts)")
                                        else:
                                            # Indented warning for format issues
                                            st.warning(f"&nbsp;&nbsp;&nbsp;&nbsp; L Unexpected task format: {task_detail}")
                            else:
                                st.warning(f" - Quest details not found: '{quest_id}'")
                        # Add slight space after the quest list if needed
                        st.write("")


                # --- Column 2: Standalone Tasks ---
                with col_tasks:
                    st.markdown("**Standalone Tasks**")
                    if not contained_tasks:
                        st.caption("No standalone tasks.")
                    else:
                        for task_id in contained_tasks:
                            task_template = task_templates.get(task_id)
                            if task_template:
                                # --- Display Task Status ---
                                current_status = utils.calculate_item_status(
                                    task_id, 'task', mission_template, mission_assignment_data
                                )
                                status_icon = "🔒" if current_status == "locked" else "✅" if current_status == "completed" else "▶️"
                                task_name = task_template.get('name', task_template.get('description', 'Unknown Task'))
                                task_emoji = task_template.get('emoji','📝')
                                task_points = task_template.get('points', 0)

                                # Display task line
                                if current_status == "completed":
                                    st.markdown(f"- {status_icon} ~~{task_emoji} {task_name} ({task_points} pts)~~")
                                elif current_status == "locked":
                                    st.markdown(f"- {status_icon} {task_emoji} {task_name} ({task_points} pts)")
                                else: # Active
                                    st.markdown(f"- {status_icon} {task_emoji} **{task_name}** ({task_points} pts)")
                                    # TODO: Button/interaction for active standalone tasks?
                            else:
                                st.warning(f" - Task details not found: '{task_id}'")
                        # Add slight space after the task list if needed
                        st.write("")

        # Add vertical space between expanders for better separation
        st.write("") # Using write adds a flexible space
        # Or use st.markdown("<br>", unsafe_allow_html=True) for more control
        
# --- NO MISSIONS ---
if not accepted_missions and not pending_missions:
    st.info("This is where the missions go!")
    st.warning("It looks like there aren't any missions assigned to you yet - you either haven't started or already finished everything!")
    st.error("If that's not the case - you should probably screenshot this and send it to Andrew.")