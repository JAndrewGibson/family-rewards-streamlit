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
mission_templates = st.session_state.get("mission_templates")
task_templates = st.session_state.get("task_templates")
points_data = st.session_state.get("points")
POINTS_FILE = 'points.json'
ASSIGNED_QUESTS_FILE = 'assignments.json'
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
     

active_mission_quests = [] # Ensure initialized
active_standalone_quests = [] # Ensure initialized
active_mission_tasks = [] # Let's gather mission tasks separately too for clarity

# --- SIDEBAR POINTS ---
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
        
# --- ACTIVE QUESTS ---      
        
# --- 1. Gather ALL Active Items ---

active_items = [] # List to hold dicts for all displayable/actionable items
# A. Active Standalone Quests
standalone_quest_assignments = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'quest' and data.get('status') == 'active'
}
for assign_id, assignment_data in standalone_quest_assignments.items():
     quest_id = assignment_data.get('quest_id') or assignment_data.get('template_id')
     quest_template = quest_templates.get(quest_id)
     if quest_template:
         active_items.append({
             "item_type": "standalone_quest", "assign_id": assign_id,
             "quest_id": quest_id, "template": quest_template,
             "task_statuses": assignment_data.get('task_status', {})
         })


# B. Active Quests & Tasks from within Accepted Missions
accepted_missions = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('type') == 'mission' and data.get('status') == 'accepted'
}
for mission_assign_id, mission_assignment_data in accepted_missions.items():
    mission_template_id = mission_assignment_data.get('template_id')
    mission_template = mission_templates.get(mission_template_id)
    if not mission_template: continue

    # Check contained Quests
    contained_quest_ids = mission_template.get('contains_quests', [])
    for quest_id in contained_quest_ids:
        quest_instance_status = utils.calculate_item_status(quest_id, 'quest', mission_template, mission_assignment_data)
        if quest_instance_status == 'active':
            quest_template = quest_templates.get(quest_id)
            if quest_template:
                # Append to active_items instead of active_mission_quests
                # Ensure the keys match what the display loop expects
                active_items.append({
                    "item_type": "mission_quest", # Add this type identifier
                    "assign_id": mission_assign_id, # Mission's assignment ID
                    "quest_id": quest_id,
                    "template": quest_template, # Use 'template' key like standalone quests
                    "task_statuses": mission_assignment_data.get('quest_instances', {}).get(quest_id, {}).get('task_status', {}),
                    "mission_template": mission_template # Keep for context display
                 })
            else:
                print(f"DEBUG:   Template NOT FOUND for '{quest_id}' in quest_templates dict!")

    # Check contained Standalone Tasks
    contained_task_ids = mission_template.get('contains_tasks', [])
    for task_id in contained_task_ids:
        task_instance_status = utils.calculate_item_status(task_id, 'task', mission_template, mission_assignment_data)
        if task_instance_status == 'active':
             task_template = task_templates.get(task_id)
             if task_template:
                 active_items.append({
                      "item_type": "mission_task", "assign_id": mission_assign_id, # Mission assignment ID
                      "task_id": task_id, "template": task_template,
                      "mission_template": mission_template # Pass mission template for context
                 })



# --- 2. Display Active Items and Buttons ---
if not active_items:
    st.info("You have no active quests or tasks right now. Check the Quest Board or Missions page!")
else:
    for item in active_items:
        item_type = item["item_type"]

        # --- Display Standalone Quest or Mission Quest ---
        if item_type == "standalone_quest" or item_type == "mission_quest":
            qt = item['template']
            quest_id = item['quest_id']
            task_statuses = item['task_statuses']
            assign_id = item['assign_id'] # This is mission_assign_id for mission_quest

            st.subheader(f"{qt.get('emoji','⚔️')} {qt.get('name','Unnamed Quest')}")
            if item_type == "mission_quest":
                 st.caption(f"Part of Mission: _{item['mission_template'].get('name', item['mission_template'])}_")
            st.caption(qt.get('description', 'No description.'))

            quest_tasks = qt.get('tasks', [])
            if not quest_tasks: st.info("No tasks defined."); continue

            st.write("**Tasks to Complete:**")
            for task in quest_tasks:
                task_id = task.get('id')
                if not task_id: continue
                task_status = task_statuses.get(task_id, 'unknown')
                task_desc = task.get('description', '...'); task_emoji = task.get('emoji', '❓'); task_points = task.get('points', 0)
                task_status_icon = "✅" if task_status == 'completed' else "⏳"

                with st.container(border=(task_status == 'pending')):
                     col_t, col_b = st.columns([4, 1])
                     with col_t: # Task Info
                          if task_status == 'completed': st.markdown(f"- {task_status_icon} ~~{task_emoji} {task_desc} ({task_points} pts)~~")
                          else: st.markdown(f"- {task_status_icon} {task_emoji} {task_desc} ({task_points} pts)")
                     with col_b: # Button Column
                          button_key = f"done_{item_type}_{assign_id}_{quest_id}_{task_id}"
                          if st.button("Done!", key=button_key, disabled=(task_status != 'pending')):
                              # --- BUTTON LOGIC ---
                              # Load fresh data
                              current_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                              current_points = utils.load_points(POINTS_FILE)
                              if current_assignments is None or current_points is None:
                                  st.error("Failed to load data before update.")
                              else:
                                  task_completed = False
                                  # Update task status in the correct place
                                  try:
                                      if item_type == "standalone_quest":
                                          current_assignments[username][assign_id]['task_status'][task_id] = 'completed'
                                          task_completed = True
                                      elif item_type == "mission_quest":
                                          current_assignments[username][assign_id]['quest_instances'][quest_id]['task_status'][task_id] = 'completed'
                                          task_completed = True
                                  except KeyError:
                                       st.error("Failed to find task to update status.")

                                  if task_completed:
                                      st.success(f"Task '{task_desc}' marked done!")
                                      # Award task points
                                      current_points[username] = current_points.get(username, 0) + task_points
                                      utils.save_points(current_points, POINTS_FILE) # Save points immediately

                                      # Check for Quest Completion
                                      quest_just_completed = utils.check_and_complete_quest_instance(
                                          username, assign_id, quest_id, current_assignments, current_points, quest_templates
                                          # Need to adapt this function slightly based on item_type if necessary
                                      )
                                      # Save points again if bonus was added
                                      if quest_just_completed: utils.save_points(current_points, POINTS_FILE)


                                      # If quest was part of mission, check mission completion & update prerequisites
                                      if item_type == "mission_quest":
                                           mission_just_completed = utils.check_and_complete_mission_instance(
                                               username, assign_id, current_assignments, current_points, mission_templates, quest_templates, task_templates
                                           )
                                           if mission_just_completed: utils.save_points(current_points, POINTS_FILE) # Save points again

                                           utils.update_prerequisites(
                                               username, assign_id, current_assignments, mission_templates
                                           )


                                      # Save assignments & update session state
                                      if utils.save_assignments(current_assignments, ASSIGNMENTS_FILE):
                                          st.session_state['assignments'] = current_assignments
                                          st.session_state['points'] = current_points # Update points in state too
                                          st.rerun()
                                      else:
                                           st.error("Failed to save progress update.")
                              # --- END BUTTON LOGIC ---

        # --- Display Standalone Task from Mission ---
        elif item_type == "mission_task":
             tt = item['template']
             task_id = item['task_id']
             assign_id = item['assign_id'] # Mission assignment ID
             task_status = "active" # Assumed active as it's in this list

             st.subheader(f"{tt.get('emoji','📝')} {tt.get('description','Unnamed Task')}")
             st.caption(f"Part of Mission: '{item['mission_template'].get('name', item['mission_template'])}'")
             st.write(f"Points: {tt.get('points', 0)}")

             button_key = f"done_{item_type}_{assign_id}_{task_id}"
             if st.button("Done!", key=button_key, disabled=(task_status != 'active')): # Should always be active here
                  # --- BUTTON LOGIC ---
                  # Load fresh data
                  current_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                  current_points = utils.load_points(POINTS_FILE)
                  if current_assignments is None or current_points is None:
                       st.error("Failed to load data before update.")
                  else:
                       task_completed = False
                       try:
                           # Update standalone task instance status within mission
                           current_assignments[username][assign_id]['task_instances'][task_id]['status'] = 'completed'
                           task_completed = True
                       except KeyError:
                            st.error("Failed to find task to update status.")

                       if task_completed:
                           st.success(f"Task '{tt.get('description')}' marked done!")
                           task_points = tt.get('points', 0)
                           current_points[username] = current_points.get(username, 0) + task_points
                           utils.save_points(current_points, POINTS_FILE)

                           # Check for Mission Completion & update prerequisites
                           mission_just_completed = utils.check_and_complete_mission_instance(
                                username, assign_id, current_assignments, current_points, mission_templates, quest_templates, task_templates
                           )
                           if mission_just_completed: utils.save_points(current_points, POINTS_FILE)

                           utils.update_prerequisites(
                                username, assign_id, current_assignments, mission_templates
                           )

                           # Save assignments & update session state
                           if utils.save_assignments(current_assignments, ASSIGNMENTS_FILE):
                               st.session_state['assignments'] = current_assignments
                               st.session_state['points'] = current_points
                               st.rerun()
                           else:
                                st.error("Failed to save progress update.")


# --- End of App ---