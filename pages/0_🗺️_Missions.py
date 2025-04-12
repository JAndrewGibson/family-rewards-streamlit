# pages/0_🗺️_Missions.py

import streamlit as st
import utils # Import shared utility functions
import time
import datetime # Needed for acceptance logic maybe?

# --- Page Configuration ---
st.set_page_config(page_title="Missions", page_icon="🗺️")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.warning("🔒 Please log in on the 'Home' page to view Missions.")
    st.stop()

# --- Load Data from Session State ---
username = st.session_state.get("username")
mission_templates = st.session_state.get("mission_templates")
quest_templates = st.session_state.get("quest_templates")
task_templates = st.session_state.get("task_templates")
assignments_data = st.session_state.get("assignments")

# File path needed for saving
ASSIGNMENTS_FILE = 'assignments.json' # Or your actual filename

# Check if all necessary data is loaded (Using more verbose checks from previous step)
error_loading = False
if not username: st.error("❌ Username not found."); error_loading = True
if mission_templates is None: st.error("❌ Mission templates missing."); error_loading = True
if quest_templates is None: st.error("❌ Quest templates missing."); error_loading = True
if task_templates is None: st.error("❌ Task templates missing."); error_loading = True
if assignments_data is None: st.error("❌ Assignments data missing."); error_loading = True
if error_loading: st.stop()

# --- Page Content ---
st.title("🗺️ Your Assigned Missions")
st.divider()

kid_assignments = assignments_data.get(username, {})

# --- 1. Pending Acceptance Section ---
st.header("📬 Incoming Missions (Pending Acceptance)")

pending_missions = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'mission' and data.get('status') == 'pending_acceptance'
}

if not pending_missions:
    st.info("No new missions waiting for your approval.")
else:
    st.write("Review these grand missions and choose to accept or decline:")
    for assign_id, mission_assignment_data in pending_missions.items():
        mission_template_id = mission_assignment_data.get('template_id')
        mission_template = mission_templates.get(mission_template_id)

        if not mission_template:
            st.error(f"Details not found for pending mission (ID: {mission_template_id}).")
            continue

        with st.container(border=True):
            st.subheader(f"{mission_template.get('emoji','🗺️')} {mission_template.get('name','Unnamed Mission')}")
            st.caption(mission_template.get('description', 'No description.'))

            # Optional: Preview contained items
            with st.expander("View Mission Components"):
                 contained_quests = mission_template.get('contains_quests', [])
                 contained_tasks = mission_template.get('contains_tasks', [])
                 if not contained_quests and not contained_tasks: st.write("No components listed.")
                 if contained_quests:
                      st.markdown("**Quests:**")
                      for q_id in contained_quests: st.write(f"- {quest_templates.get(q_id,{}).get('name',q_id)}")
                 if contained_tasks:
                      st.markdown("**Tasks:**")
                      for t_id in contained_tasks: st.write(f"- {task_templates.get(t_id,{}).get('description',t_id)}")

            st.markdown(f"**Completion Reward:** {mission_template.get('completion_reward', {}).get('points', 0)} points. {mission_template.get('completion_reward', {}).get('description', '')}")

            # Action Buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Accept Mission", key=f"accept_m_{assign_id}", use_container_width=True):
                    current_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                    if username in current_assignments and assign_id in current_assignments[username]:
                        # --- Logic on Acceptance ---
                        current_assignments[username][assign_id]['status'] = 'accepted'
                        # Initialize instance dictionaries if they don't exist
                        current_assignments[username][assign_id].setdefault('quest_instances', {})
                        current_assignments[username][assign_id].setdefault('task_instances', {})
                        # Optional: Pre-populate initial 'locked'/'active' status based on utils.calculate_item_status,
                        # or just let the display logic calculate it dynamically. Dynamic is simpler.

                        if utils.save_assignments(current_assignments, ASSIGNMENTS_FILE):
                            st.session_state['assignments'] = current_assignments
                            st.success(f"Mission '{mission_template.get('name')}' accepted!")
                            time.sleep(1)
                            st.rerun()
                    else:
                         st.error("Could not find mission assignment to accept.")

            with col2:
                 if st.button("❌ Decline Mission", key=f"decline_m_{assign_id}", use_container_width=True):
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
        st.divider()


# --- 2. Accepted Missions Section ---
st.header("🎯 Accepted Missions")

accepted_missions = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'mission' and data.get('status') == 'accepted'
}

if not accepted_missions:
    st.info("You haven't accepted any missions yet. Check the pending section!")
else:
    st.write(f"Here are your current missions ({len(accepted_missions)}):")
    st.markdown("---")

    for assign_id, mission_assignment_data in accepted_missions.items():
        mission_template_id = mission_assignment_data.get('template_id')
        mission_template = mission_templates.get(mission_template_id)

        if not mission_template:
            st.error(f"Could not find template details for Mission ID {mission_template_id}. Skipping.")
            continue

        # Display Mission Header
        st.subheader(f"{mission_template.get('emoji','🗺️')} {mission_template.get('name','Unnamed Mission')}")
        st.caption(mission_template.get('description', 'No description.'))
        # TODO: Add overall mission progress calculation later

        # --- Display Contained Quests & Tasks with Status ONLY ---
        st.markdown("**Mission Components Overview:**")
        contained_quests = mission_template.get('contains_quests', [])
        contained_tasks = mission_template.get('contains_tasks', [])

        if not contained_quests and not contained_tasks:
            st.info("This mission has no defined components in its template.")
            st.markdown("---")
            continue

        # Display Contained Quests Status
        if contained_quests:
            st.markdown("**Quests:**")
            for quest_id in contained_quests:
                quest_template = quest_templates.get(quest_id)
                if quest_template:
                    current_status = utils.calculate_item_status(
                        quest_id, 'quest', mission_template, mission_assignment_data
                    )
                    status_icon = "🔒" if current_status == "locked" else "✅" if current_status == "completed" else "▶️"
                    quest_name = quest_template.get('name', 'Unknown Quest')
                    quest_emoji = quest_template.get('emoji','⚔️')
                    # Display Status ONLY - Interaction moved to Active Quests page
                    if current_status == "completed":
                         st.write(f"- {status_icon} ~~{quest_emoji} {quest_name}~~ *(Completed)*")
                    elif current_status == "locked":
                         st.write(f"- {status_icon} {quest_emoji} {quest_name} *(Locked)*")
                    else: # Active
                         st.write(f"- {status_icon} {quest_emoji} **{quest_name}** *(Active)*") # Guide user
                else:
                    st.warning(f"  - Details for Quest ID '{quest_id}' not found.")

        # Display Contained Standalone Tasks Status
        if contained_tasks:
            st.markdown("**Standalone Tasks:**")
            for task_id in contained_tasks:
                task_template = task_templates.get(task_id)
                if task_template:
                    current_status = utils.calculate_item_status(
                        task_id, 'task', mission_template, mission_assignment_data
                    )
                    status_icon = "🔒" if current_status == "locked" else "✅" if current_status == "completed" else "▶️"
                    task_desc = task_template.get('description', 'Unknown Task')
                    task_emoji = task_template.get('emoji','📝')
                    task_points = task_template.get('points', 0)
                    # Display Status and info - Button interaction for active tasks needed here eventually too?
                    # For now, let's simplify and assume standalone tasks are marked done elsewhere or add button later.
                    if current_status == "completed":
                         st.write(f"- {status_icon} ~~{task_emoji} {task_desc} ({task_points} pts)~~ *(Completed)*")
                    elif current_status == "locked":
                         st.write(f"- {status_icon} {task_emoji} {task_desc} ({task_points} pts) *(Locked)*")
                    else: # Active
                         st.write(f"- {status_icon} {task_emoji} **{task_desc}** ({task_points} pts) *(Active)*") # Need button here eventually
                else:
                    st.warning(f"  - Details for Task ID '{task_id}' not found.")

        st.markdown("---") # Separator between missions