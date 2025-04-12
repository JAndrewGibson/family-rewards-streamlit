# pages/2_🚀_Active_Quests.py

import streamlit as st
import utils # Import shared utility functions

# --- Page Configuration ---
st.set_page_config(page_title="Active Quests", page_icon="🚀")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.warning("🔒 Please log in on the Home page to view your Active Quests.")
    st.stop() # Do not render anything else on this page
# --- End Authentication Check ---

# --- Load Data from Session State ---
username = st.session_state.get("username")
# Load all templates needed for context
mission_templates = st.session_state.get("mission_templates")
quest_templates = st.session_state.get("quest_templates")
task_templates = st.session_state.get("task_templates") # Needed if showing task points?
assignments_data = st.session_state.get("assignments")

ASSIGNMENTS_FILE = 'assignments.json'

# Check if all necessary data is loaded
error_loading = False
if not username: st.error("❌ Username not found."); error_loading = True
if mission_templates is None: st.error("❌ Mission templates missing."); error_loading = True
if quest_templates is None: st.error("❌ Quest templates missing."); error_loading = True
if task_templates is None: st.error("❌ Task templates missing."); error_loading = True # Need tasks for points display
if assignments_data is None: st.error("❌ Assignments data missing."); error_loading = True
if error_loading: st.stop()

if not username or quest_templates is None or assignments_data is None:
     st.error("Required data not found. Please ensure you are logged in and data files are loaded.")
     st.stop()

# --- Page Content ---
st.title("🚀 Your Active Quests")
st.write("This board shows quests you can currently work on, primarily from your accepted Missions.")
st.divider()

kid_assignments = assignments_data.get(username, {})
# --- 1. Gather Active Quests from Missions ---
active_mission_quests = []
accepted_missions = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'mission' and data.get('status') == 'accepted'
}

for mission_assign_id, mission_assignment_data in accepted_missions.items():
    mission_template_id = mission_assignment_data.get('template_id')
    mission_template = mission_templates.get(mission_template_id)
    if not mission_template: continue # Skip if mission template missing

    contained_quest_ids = mission_template.get('contains_quests', [])
    for quest_id in contained_quest_ids:
        # Calculate status of this quest instance within this mission assignment
        quest_instance_status = utils.calculate_item_status(
            quest_id, 'quest', mission_template, mission_assignment_data
        )

        if quest_instance_status == 'active':
            quest_template = quest_templates.get(quest_id)
            if quest_template:
                # Store relevant info for display
                active_mission_quests.append({
                    'mission_assign_id': mission_assign_id,
                    'mission_template_id': mission_template_id,
                    'mission_name': mission_template.get('name', mission_template_id),
                    'quest_id': quest_id,
                    'quest_template': quest_template,
                    # Get the task statuses for this specific quest instance
                    'task_statuses': mission_assignment_data.get('quest_instances', {}).get(quest_id, {}).get('task_status', {})
                })

# --- 2. Gather Active Standalone Quests ---
active_standalone_quests = []
standalone_quest_assignments = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'quest' and data.get('status') == 'active'
}
for assign_id, assignment_data in standalone_quest_assignments.items():
     quest_id = assignment_data.get('quest_id') or assignment_data.get('template_id')
     quest_template = quest_templates.get(quest_id)
     if quest_template:
         active_standalone_quests.append({
             'assign_id': assign_id,
             'quest_id': quest_id,
             'quest_template': quest_template,
             'task_statuses': assignment_data.get('task_status', {})
         })


# --- 3. Display Active Quests ---

if not active_mission_quests and not active_standalone_quests:
    st.info("You have no active quests right now. Check the Quest Board for pending quests or the Missions page for locked items!")
else:
    # --- Display Quests from Missions (Primary) ---
    if active_mission_quests:
        st.header("From Your Missions")
        for quest_info in active_mission_quests:
            qt = quest_info['quest_template'] # shortcut for quest template
            st.subheader(f"{qt.get('emoji','⚔️')} {qt.get('name','Unnamed Quest')}")
            st.caption(f"Part of Mission: '{quest_info['mission_name']}'")
            st.caption(qt.get('description', 'No description.'))

            quest_tasks = qt.get('tasks', [])
            current_task_statuses = quest_info['task_statuses']

            if not quest_tasks:
                st.info("This quest has no defined tasks.")
            else:
                st.write("**Tasks to Complete:**")
                for task in quest_tasks:
                    task_id = task.get('id')
                    if not task_id: continue

                    task_status = current_task_statuses.get(task_id, 'unknown')
                    task_desc = task.get('description', '...')
                    task_emoji = task.get('emoji', '❓')
                    task_points = task.get('points', 0)
                    task_status_icon = "✅" if task_status == 'completed' else "⏳"

                    with st.container(border=(task_status == 'pending')):
                         col_t, col_b = st.columns([4, 1])
                         with col_t:
                             if task_status == 'completed':
                                  st.markdown(f"- {task_status_icon} ~~{task_emoji} {task_desc} ({task_points} pts)~~")
                             else:
                                  st.markdown(f"- {task_status_icon} {task_emoji} {task_desc} ({task_points} pts)")
                         with col_b:
                              # Button to mark task within mission quest done
                              st.button(
                                  "Done!",
                                  key=f"done_mission_{quest_info['mission_assign_id']}_q_{quest_info['quest_id']}_t_{task_id}", # Include mission context
                                  disabled=(task_status != 'pending'),
                                  help="Complete this task step!"
                              )
            st.markdown("---") # Separator between quests

    # --- Display Standalone Quests (Secondary) ---
    if active_standalone_quests:
        st.header("Standalone Quests")
        for quest_info in active_standalone_quests:
            qt = quest_info['quest_template'] # shortcut
            st.subheader(f"{qt.get('emoji','⚔️')} {qt.get('name','Unnamed Quest')}")
            # No mission context needed here
            st.caption(qt.get('description', 'No description.'))

            quest_tasks = qt.get('tasks', [])
            current_task_statuses = quest_info['task_statuses']

            if not quest_tasks:
                st.info("This quest has no defined tasks.")
            else:
                 st.write("**Tasks to Complete:**")
                 # (Duplicate task display logic from above - consider making a function)
                 for task in quest_tasks:
                    task_id = task.get('id')
                    if not task_id: continue
                    task_status = current_task_statuses.get(task_id, 'unknown')
                    task_desc = task.get('description', '...')
                    task_emoji = task.get('emoji', '❓')
                    task_points = task.get('points', 0)
                    task_status_icon = "✅" if task_status == 'completed' else "⏳"
                    with st.container(border=(task_status == 'pending')):
                         col_t, col_b = st.columns([4, 1])
                         with col_t:
                            if task_status == 'completed': st.markdown(f"- {task_status_icon} ~~{task_emoji} {task_desc} ({task_points} pts)~~")
                            else: st.markdown(f"- {task_status_icon} {task_emoji} {task_desc} ({task_points} pts)")
                         with col_b:
                              # Button to mark task within standalone quest done
                              st.button(
                                  "Done!",
                                  key=f"done_quest_{quest_info['assign_id']}_t_{task_id}", # Simpler key
                                  disabled=(task_status != 'pending'),
                                  help="Complete this task step!"
                              )
            st.markdown("---")


# --- End of App ---