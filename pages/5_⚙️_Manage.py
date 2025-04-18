import streamlit as st
import utils # Import shared utility functions
from datetime import datetime, timezone
import time # For assignment ID generation
from pathlib import Path
import json
import os
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="Manage", page_icon="⚙️")
st.title("⚙️ Manage")

# --- Authentication & Authorization Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("home.py")

# --- Constants for filenames ---
TASKS_TEMPLATE_FILE = 'tasks.json'
QUESTS_TEMPLATE_FILE = 'quests.json'
MISSIONS_TEMPLATE_FILE = 'missions.json'
ASSIGNED_QUESTS_FILE = 'assignments.json'
HISTORY_FOLDER = Path("user_history")
HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)


# --- Load Data (Load fresh for management/assignment actions) ---
# Use .get() from session state for config, but load templates/assignments fresh
config = st.session_state.get("config")
username = st.session_state.get("username") # Logged-in parent's username
name = st.session_state['name']

if not config or not username or not name:
     st.error("User configuration not found in session state. Please log in again.")
     time.sleep(2)
     st.switch_page("home.py")



# --- Load Existing Templates (Load fresh each time or use session state carefully) ---
task_templates = utils.load_task_templates(TASKS_TEMPLATE_FILE)
quest_templates = utils.load_quest_templates(QUESTS_TEMPLATE_FILE)
mission_templates = utils.load_mission_templates(MISSIONS_TEMPLATE_FILE)
assignments_data = utils.load_assignments(ASSIGNED_QUESTS_FILE)
firstname = utils.first_name(name)
safe_filename = f"{firstname}_history.json"
history_file_path = HISTORY_FOLDER / safe_filename

current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"
st.sidebar.metric("My Points", current_points)
st.sidebar.divider()

if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

def get_item_display_name(item_id, q_templates, t_templates):
    """Gets a display name for a quest or task ID."""
    quest_info = q_templates.get(item_id)
    if quest_info:
        return f"Quest: {quest_info.get('name', item_id)} ({quest_info.get('quest_combined_points')} pts)"
    task_info = t_templates.get(item_id)
    if task_info:
        return f"Task: {task_info.get('description', item_id)} ({task_info.get('points')} pts)"
    return item_id # Fallback

# Handle loading errors
if task_templates is None or quest_templates is None or mission_templates is None or assignments_data is None:
    st.error("Failed to load one or more data files. Cannot proceed.")
    st.stop()



# --- PARENT/ADMIN ---
if st.session_state.get('role') == 'parent' or st.session_state.get('role') == 'admin':
    # --- Define Tabs ---
    tab_list = [
        "📝 Tasks",
        "⚔️ Quests",
        "🗺️ Missions",
        "💎 Rewards",
        "🎯 Assign",
        "🗝️ History"
    ]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_list)

    # --- Manage Tasks Tab ---
    with tab1:
        st.header("📝 Standalone Task Form")
        st.write("Define individual tasks.")

        # Display existing tasks (optional enhancement)
        with st.expander("View Existing Task Templates"):
            if not task_templates:
                st.info("No standalone task templates defined yet.")
            else:
                for task_id, task_data in task_templates.items():
                    st.write(f"**{task_data.get('name','')}** ({task_data.get('points',0)} pts): {task_data.get('emoji','')} {task_data.get('description','')}")

        st.divider()
        st.subheader("Create New Task Template")

        # Use a form for better state management on creation
        with st.form("new_task_form", clear_on_submit=True):
            new_task_id = st.text_input("Task ID (must be unique):")
            new_task_name = st.text_input("Task Name")
            new_task_desc = st.text_area("Description:")
            new_task_points = st.number_input("Points:", min_value=0, step=1, value=10)
            new_task_emoji = st.text_input("Emoji Icon:", max_chars=2)

            submitted_task = st.form_submit_button("Save Task Template")
            if submitted_task:
                # Validation
                if not new_task_id:
                    st.error("Task ID cannot be empty.")
                elif not new_task_name:
                    st.error("Task Name cannot be empty")
                elif not new_task_desc:
                    st.error("Task description cannot be empty.")
                elif new_task_id in task_templates:
                    st.error(f"Task ID '{new_task_id}' already exists. Please choose a unique ID.")
                else:
                    # Add to data structure
                    task_templates[new_task_id] = {
                        "name": new_task_name,
                        "description": new_task_desc,
                        "points": new_task_points,
                        "emoji": new_task_emoji,
                        "created_by": username
                    }
                    
                    # Attempt to save
                    if utils.save_task_templates(task_templates, TASKS_TEMPLATE_FILE):
                        st.success(f"Task template **{new_task_name}** - *{new_task_desc}* ({new_task_id}), saved successfully!")
                        # --- BEGIN HISTORY LOGGING FOR TASK CREATION ---
                        try:
                            # Ensure firstname is available (should be if user is logged in)
                            if not username:
                                st.warning("Could not log task creation event: User information not found. Please screenshot and tell Andrew.")
                            else:
                                # Create the event data
                                now_utc = datetime.now(timezone.utc)
                                timestamp_iso = now_utc.isoformat()
                                task_creation_event = {
                                    "timestamp": timestamp_iso,
                                    "event_type": "task_created",
                                    "user": username,
                                    "affected_item": new_task_id,
                                    "message": f"{username} created new task '{new_task_name}'."
                                }

                                # --- Read current history ---
                                current_history = []
                                if history_file_path.is_file(): # Check if file exists before reading
                                    try:
                                        with open(history_file_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                            if content:
                                                current_history = json.loads(content)
                                                if not isinstance(current_history, list):
                                                    print(f"Warning: History file {history_file_path} was not a list. Resetting for append.") # Server log
                                                    current_history = []
                                            # If content is empty, current_history remains []
                                    except json.JSONDecodeError:
                                        print(f"Warning: History file {history_file_path} contained invalid JSON. Resetting for append.") # Server log
                                        current_history = []
                                    except OSError as e:
                                        st.warning(f"Could not read history file to log task creation: {e}")
                                        current_history = None # Signal error state
                                # If file didn't exist, current_history remains []

                                # --- Append and Write back (only if read was successful or file didn't exist) ---
                                if current_history is not None:
                                    current_history.append(task_creation_event)
                                    try:
                                        with open(history_file_path, 'w', encoding='utf-8') as f:
                                            json.dump(current_history, f, indent=4)
                                        print(f"Logged task_created event for {firstname}, task ID {new_task_id}. {new_task_emoji}") # Server log
                                    except OSError as e:
                                        st.warning(f"Could not write history file to log task creation: {e}")

                        except Exception as e:
                            # Catch any unexpected errors during history logging
                            st.warning(f"An error occurred while logging task creation to history: {e}")
                        # --- END HISTORY LOGGING FOR TASK CREATION ---
                    else:
                        # Error message handled by save function, remove potentially corrupt data
                        del task_templates[new_task_id] # Roll back change if save failed
                    

    # --- Tab 2: Manage Quests ---
    with tab2:
        st.header("⚔️ Quest Form")
        st.caption("Define quests composed of multiple steps (tasks defined within).")

        with st.expander("View Existing Quest Templates"):
            if not quest_templates:
                st.info("No quest templates defined yet.")
            else:
                for quest_id, quest_data in quest_templates.items():
                    col1, col2 = st.columns([3,1])
                    with col1:
                        st.write(f"**{quest_data.get('name','')}** ({quest_data.get('quest_combined_points','')} pts): {quest_data.get('emoji','')} {quest_data.get('description','')}")
                        with col2:
                            if st.checkbox ("See details", key=quest_id):
                                with col1:
                                    tasks = quest_data.get('tasks',[])
                                    for task in tasks:
                                        st.write(f"- {task.get('emoji','')} **{task.get('name','')}** ({task.get('points','')} pts): - {task.get('description','')}")
                                    st.badge(f"**Completion points: {quest_data.get('completion_bonus_points')}**", color="blue")
                    # Add delete button functionality here later if needed

        st.divider()
        st.subheader("Create or Edit Quest Template") # Changed subheader slightly

        # Initialize session state list for tasks in the current quest being built/edited
        if 'current_quest_tasks' not in st.session_state:
            st.session_state.current_quest_tasks = []


        with st.form("new_quest_form"): # Don't clear on submit automatically
            st.write("**Quest Details:**")
            cols2 = st.columns([4,4])
            new_quest_id = cols2[0].text_input("Quest ID (must be unique):", key="quest_form_id")
            new_quest_name = cols2[1].text_input("Quest Name:", key="quest_form_name")
            new_quest_desc = st.text_area("Description:", key="quest_form_desc",)
            cols3 = st.columns([4,4])
            new_quest_emoji = cols3[0].text_input("Emoji Icon:", max_chars=2, key="quest_form_emoji")
            new_quest_bonus = cols3[1].number_input("Completion Bonus Points:", min_value=0, step=50, value=0, key="quest_form_bonus",)
            total_points = st.session_state.quest_form_bonus
            
            
            # Display input fields for tasks currently in session state
            tasks_to_render = st.session_state.current_quest_tasks
            for i, task_data in enumerate(tasks_to_render):
                cols1 = st.columns([1,4])
                cols1[0].subheader(f"**Task #{i+1}**")
                cols1[1].divider()
                cols = st.columns([3, 4, 2,]) # Adjust ratios as needed
                # Use default values from session state for potential pre-filling
                task_data['id'] = cols[0].text_input(f"Task ID", value=task_data.get('id',''), key=f"q_task_id_{i}")
                task_data['name'] = cols[0].text_input(f"Task Name", value=task_data.get('name',''), key=f"q_task_name_{i}")
                task_data['description'] = cols[1].text_area(f"Task Description", value=task_data.get('description',''), key=f"q_task_desc_{i}", height=122)
                task_data['points'] = cols[2].number_input(f"Points", min_value=0, step=50, value=task_data.get('points',0), key=f"q_task_points_{i}")
                task_data['emoji'] = cols[2].text_input(f"Emoji", value=task_data.get('emoji',''), max_chars=2, key=f"q_task_emoji_{i}")
                total_points += st.session_state.get(f"q_task_points_{i}", "")
                # Note: This directly modifies the dict in session state IF it's mutable,
                # but reading back from widget keys during submission is more robust.


            # Save Quest Button (inside the form)
            submitted_quest = st.form_submit_button("💾 Save Quest Template")
            if submitted_quest:
                # --- Reconstruct Task List from Form Inputs ---
                final_tasks = []
                valid_tasks = True
                num_task_steps = len(st.session_state.current_quest_tasks) # How many rows of inputs exist

                for i in range(num_task_steps):
                    task_id = st.session_state.get(f"q_task_id_{i}", "").strip()
                    task_name = st.session_state.get(f"q_task_name_{i}").strip()
                    task_desc = st.session_state.get(f"q_task_desc_{i}", "").strip()
                    task_points = st.session_state.get(f"q_task_points_{i}", 0)
                    task_emoji = st.session_state.get(f"q_task_emoji_{i}", "")

                    # Basic validation for each task step
                    if not task_id:
                        st.error(f"Task Step {i+1}: ID cannot be empty.")
                        valid_tasks = False
                    if not task_name:
                        st.error(f"Task Name {i+1}: Name cannot be empty")
                    if not task_desc:
                        st.error(f"Task Step {i+1}: Description cannot be empty.")
                        valid_tasks = False
                    # Add check for unique task IDs within this quest? (Advanced)

                    final_tasks.append({
                        "id": task_id,
                        "name":task_name,
                        "description": task_desc,
                        "points": task_points,
                        "emoji": task_emoji
                    })

                # --- Validate Quest Shell & Save ---
                quest_id = st.session_state.quest_form_id.strip()
                quest_name = st.session_state.quest_form_name.strip()

                if not quest_id or not quest_name:
                    st.error("Quest ID and Quest Name cannot be empty.")
                elif quest_id in quest_templates: # Simple check for existing ID
                    st.error(f"Quest ID '{quest_id}' already exists. Choose a unique ID.")
                elif not valid_tasks:
                    st.error("Please fix the errors in the task steps above.")
                else:
                    # Proceed to save
                    quest_templates[quest_id] = {
                        "name": quest_name,
                        "description": st.session_state.quest_form_desc,
                        "emoji": st.session_state.quest_form_emoji,
                        "tasks": final_tasks,
                        "completion_bonus_points": st.session_state.quest_form_bonus,
                        "quest_combined_points": total_points,
                        "created_by": username
                    }
                    if utils.save_quest_templates(quest_templates, QUESTS_TEMPLATE_FILE):
                        st.success(f"Quest template **{quest_data.get('name','')}** saved successfully!")
                        # --- BEGIN HISTORY LOGGING FOR QUEST CREATION ---
                        try:
                            if not username:
                                st.warning("Could not log quest creation event: User Information not found. Please screenshot and tell Andrew.")
                            else:
                                now_utc = datetime.now(timezone.utc)
                                timestamp_iso = now_utc.isoformat()
                                quest_creation_event = {
                                    "timestamp": timestamp_iso,
                                    "event_type": "quest_created",
                                    "user": username,
                                    "affected_item": new_quest_id,
                                    "message": f"{username} created new quest '{new_quest_name}'."
                                }
                                
                                current_history = []
                                if history_file_path.is_file():
                                    try:
                                        with open(history_file_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                            if content:
                                                current_history = json.loads(content)
                                                if not isinstance(current_history, list):
                                                    print(f"Warning: History file {history_file_path} was not a list. Resetting for append.")
                                                    current_history = []
                                    except json.JSONDecodeError:
                                        print(f"Warning: History file {history_file_path} contained invalid JSON. Resetting for append.")
                                        current_history = []
                                    except OSError as e:
                                        st.warning(f"Could not read history file to log quest creation: {e}")
                                        current_history = None
                                if current_history is not None:
                                    current_history.append(quest_creation_event)
                                    try:
                                        with open(history_file_path, 'w', encoding= 'utf-8') as f:
                                            json.dump(current_history, f, indent=4)
                                        print(f"Logged quest_created event for {firstname}, quest ID {new_quest_id}. {new_quest_emoji}")
                                    except OSError as e:
                                        st.warning(f"could not write history file to log quest creation: {e}")
                        except Exception as e:
                            st.warning(f"An error occured while logging quest creation to history: {e}")
                    
                        # Clear the task list in session state for the next creation
                        st.session_state.current_quest_tasks = []
                        # We might need to rerun to clear the main form fields if clear_on_submit isn't working as expected
                        time.sleep(2)
                        st.rerun() # Use if form fields don't clear properly
                    else:
                        #SAVE FAILED! ROLLING BACK
                        st.error("Saving failed. Please check permissions or logs.")
                        del quest_templates[new_quest_id] # Remove quest 

        # --- "Add Task Step" Button (Outside the form) ---
        if st.button("➕ Add Task Step to Quest Definition"):
            # Add a new blank task structure to the list in session state
            st.session_state.current_quest_tasks.append({"id": "", "description": "", "points": 0, "emoji": ""})
            st.rerun()

    # --- Tab 3: Manage Missions ---
    with tab3:
        st.header("🗺️ Mission Templates")
        st.write("Define large goals containing Quests and/or standalone Tasks.")

        with st.expander("View Existing Mission Templates"):
            if not mission_templates:
                st.info("No mission templates defined yet.")
            else:
                for mission_id, mission_data in mission_templates.items():
                        col1, col2 = st.columns([3,1])
                        quest_column, task_column = st.columns([3,3])
                        with col1:
                            rewards = mission_data.get('completion_reward', {})
                            st.write(f"**{mission_data.get('name','')}** ({mission_data.get('mission_combined_points', '')} pts): {mission_data.get('emoji','')} {mission_data.get('description','')}")
                            quests_in_mission = mission_data.get('contains_quests', [])
                            tasks_in_mission = mission_data.get('contains_tasks', [])
                            with col2:
                                if st.checkbox("See details", key=mission_id):
                                    with quest_column:
                                        if quests_in_mission:
                                            st.write("**Quests in this missions:**")
                                            for quest_id in quests_in_mission:
                                                quest_info = quest_templates.get(quest_id)
                                                if quest_info:
                                                    st.write(f"- {quest_info.get('name','')} ({quest_info.get('quest_combined_points', '')} pts)")
                                                    st.write(f"- - {quest_info.get('description','')}")
                                                else:
                                                    st.warning(f"Quest ID {quest_id} not found in quest templates. This error should never exist - tell Andrew immeditely. lol")
                                        else:
                                            st.write("**This mission contains no quests**")
                                        st.badge(f"Completion points: {rewards.get('points')}",)
                                    with task_column:        
                                        if tasks_in_mission:
                                            st.write("**Standalone Tasks in this Mission**")
                                            for task_id in tasks_in_mission:
                                                task_info = task_templates.get(task_id)
                                                if task_info:
                                                        st.write(f"- {task_info.get('name','')} ({task_info.get('points', '')} pts)")
                                                        st.write(f"- - {task_info.get('description','')}")
                                                else:
                                                    st.write(f"No standalone tasks in this mission")

        st.divider()
        st.subheader("Create New Mission Template")

        # Use a single form for the entire mission creation including prerequisites
        with st.form("new_mission_form", clear_on_submit=False):
            new_mission_id = st.text_input("Mission ID (unique, e.g., 'mission_summer_reading'):",key="new_mission_id")
            new_mission_name = st.text_input("Mission Name:", key="new_mission_name")
            new_mission_desc = st.text_area("Description:", key="new_mission_desc")
            new_mission_emoji = st.text_input("Emoji Icon:", max_chars=4, key="new_mission_emoji")
            st.divider()

            # --- Select Contained Items ---
            st.markdown("**Select Components for this Mission:**")
            quest_options_map = {qid: get_item_display_name(qid, quest_templates, task_templates) for qid in quest_templates}
            selected_quest_ids = st.multiselect(
                "Include Quests:",
                options=list(quest_options_map.keys()),
                format_func=lambda qid: quest_options_map[qid],
                key="mission_quests_select"
            )

            task_options_map = {tid: get_item_display_name(tid, quest_templates, task_templates) for tid in task_templates}
            selected_task_ids = st.multiselect(
                "Include Standalone Tasks:",
                options=list(task_options_map.keys()),
                format_func=lambda tid: task_options_map[tid],
                key="mission_tasks_select"
            )

            # Combine all selected items for prerequisite definition
            all_selected_items = selected_quest_ids + selected_task_ids
            all_selected_items_map = { # Map IDs to display names for dropdown options
                item_id: get_item_display_name(item_id, quest_templates, task_templates)
                for item_id in all_selected_items
            }

            #st.button(label= "Refresh", icon='🔃')

            st.divider()

            # --- Define Prerequisites (Only if items are selected) ---
            if all_selected_items:
                st.subheader("Define Prerequisites (Optional)")
                st.caption("For each item below, select any other items *within this mission* that must be completed *before* it becomes active.")
                st.form_submit_button("🔄 Reload Prerequisite Options", help="Click after updating quests/tasks above to show prerequisite settings.")

                # Loop through each selected item to define its prerequisites
                for item_id in all_selected_items:
                    # Potential prerequisites are all *other* selected items
                    potential_prereqs = [p_id for p_id in all_selected_items if p_id != item_id]
                    prereq_options_map = {
                        p_id: all_selected_items_map[p_id] for p_id in potential_prereqs
                    }

                    if potential_prereqs: # Only show multiselect if there are potential prereqs
                        st.multiselect(
                            f"Prerequisites for '{all_selected_items_map[item_id]}':",
                            options=list(prereq_options_map.keys()),
                            format_func=lambda p_id: prereq_options_map[p_id],
                            key=f"prereq_{item_id}" # Unique key for each item's prereqs
                        )
                    else:
                        # Optional: Display message if no other items to select as prereqs
                        # st.write(f"No other items available to set as prerequisites for '{all_selected_items_map[item_id]}'.")
                        pass # Or just show nothing

            else:
                st.info("Select Quests or Tasks above to define prerequisites.")
                st.form_submit_button("🔄 Load Prerequisite Options", help="Click after selecting quests/tasks above to show prerequisite settings.")


            st.divider()
            # --- Completion Reward ---
            st.subheader("Mission Completion Reward")
            completion_points = st.number_input("Completion Points Reward:", min_value=0, step=100, value=0, key="completion_points") 
            completion_desc = st.text_input("Other Reward Description (optional):", key="completion_desc")

            # --- Submit Button ---
            submitted_mission = st.form_submit_button("💾 Save Mission Template")
            if submitted_mission:
                # --- Validation ---
                final_selected_quests = st.session_state.get("mission_quests_select", [])
                final_selected_tasks = st.session_state.get("mission_tasks_select", [])
                final_all_selected = final_selected_quests + final_selected_tasks
                # Read other form fields from session state using their keys
                mission_id = st.session_state.get("new_mission_id", "").strip()
                mission_name = st.session_state.get("new_mission_name", "").strip()
                mission_desc = st.session_state.get("new_mission_desc", "")
                mission_emoji = st.session_state.get("new_mission_emoji", "")
                completion_points = st.session_state.get("completion_points", 0)
                completion_desc = st.session_state.get("completion_desc", "")
                calculated_combined_points = int(completion_points)
                
                # --- ADDING POINTS FROM QUESTS AND TASKS ---
                for quest_id in final_selected_quests:
                    quest_data = quest_templates.get(quest_id) # Fetch quest data
                    if quest_data:
                        quest_pts = quest_data.get('quest_combined_points', 0)
                        try:
                            calculated_combined_points += int(quest_pts)
                        except (ValueError, TypeError):
                            st.warning(f"Quest '{quest_id}' ('{quest_data.get('name', 'Unknown')}') has non-numeric 'quest_combined_points' ({quest_pts}). Skipping points.")
                            print(f"Warning: Non-numeric quest_combined_points for quest {quest_id}: {quest_pts}")
                # Add points from selected standalone tasks
                for task_id in final_selected_tasks:
                    task_data = task_templates.get(task_id) # Fetch task data
                    if task_data:
                        # Get 'points', default to 0 if missing or not a number
                        task_pts = task_data.get('points', 0)
                        try:
                            calculated_combined_points += int(task_pts)
                        except (ValueError, TypeError):
                            st.warning(f"Task '{task_id}' ('{task_data.get('name', 'Unknown')}') has non-numeric 'points' ({task_pts}). Skipping points.")
                            # Optionally log this error for debugging
                            print(f"Warning: Non-numeric points for task {task_id}: {task_pts}")


                # Basic validation test
                valid_to_save = True
                if not mission_id or not mission_name:
                    st.error("Mission ID and Name cannot be empty.")
                    valid_to_save = False
                elif mission_id in mission_templates:
                    st.error(f"Mission ID '{mission_id}' already exists.")
                    valid_to_save = False
                elif not final_all_selected:
                    st.warning("The mission should contain at least one Quest or Task.")
                    valid_to_save = False

                if valid_to_save:
                    # --- Collect Prerequisite Data ---
                    prerequisites_dict = {}
                    for item_id in final_all_selected:
                        prereq_key = f"prereq_{item_id}"
                        selected_prereqs = st.session_state.get(prereq_key, [])
                        prerequisites_dict[item_id] = selected_prereqs

                    # --- Construct Mission Data ---
                    mission_templates[mission_id] = {
                        "name": mission_name,
                        "description": mission_desc,
                        "emoji": mission_emoji,
                        "contains_quests": final_selected_quests,
                        "contains_tasks": final_selected_tasks,
                        "prerequisites": prerequisites_dict,
                        "completion_reward": {"points": completion_points, "description": completion_desc },
                        "mission_combined_points": calculated_combined_points,
                        "created_by": username
                    }

                    # --- Save ---
                    if utils.save_mission_templates(mission_templates, MISSIONS_TEMPLATE_FILE):
                        st.success(f"{mission_name} saved successfully!")
                        #Logging logic
                        try:
                            if not username:
                                st.warning("Could not log mission creation event: User Information not found. Please screenshot and tell Andrew.")
                            else:
                                now_utc = datetime.now(timezone.utc)
                                timestamp_iso = now_utc.isoformat()
                                mission_creation_event = {
                                    "timestamp": timestamp_iso,
                                    "event_type": "mission_created",
                                    "user": username,
                                    "affected_item": new_mission_id,
                                    "message": f"{username} created new mission '{new_mission_name}'."
                                }

                                current_history = []
                                if history_file_path.is_file():
                                    try:
                                        with open(history_file_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                            if content:
                                                current_history = json.loads(content)
                                                if not isinstance(current_history, list):
                                                    print(f"Warning: History file {history_file_path} was not a list. Resetting for append.")
                                                    current_history = []
                                    except json.JSONDecodeError:
                                        print(f"Warning: History file {history_file_path} contained invalid JSON. Resetting for append.")
                                        current_history = []
                                    except OSError as e:
                                        st.warning(f"Could not read history file to log mission creation: {e}")
                                        current_history = None
                                if current_history is not None:
                                    current_history.append(mission_creation_event)
                                    try:
                                        with open(history_file_path, 'w', encoding='utf-8') as f:
                                            json.dump(current_history, f, indent=4)
                                        print(f"Logged mission_created event for {firstname}, mission ID {new_mission_id}. {new_mission_emoji}")
                                    except OSError as e:
                                        st.warning(f"Could not write history file to log mission creation: {e}")
                        except Exception as e:
                            st.warning(f"An error occured while logging mission creation to history: {e}")
                        time.sleep(2)
                        st.rerun()

                    else:
                        # Save failed, roll back if needed
                        if mission_id in mission_templates: del mission_templates[mission_id]
                        # Error message is shown by save function
    
    
            with tab4:
                st.header("Create rewards!")
                with st.form("new_reward_form", clear_on_submit=True):
                    new_reward_id = st.text_input("Reward ID")
                    new_reward_name = st.text_input("Reward Name")
                    new_reward_description = st.text_area("Description:")
                    new_reward_points = st.number_input("Points:", min_value=0, step=1, value=0)
                    new_reward_image = st.text_input("Place the URL to the image here!", placeholder="https://fastly.picsum.photos/id/912/200/300.jpg")
                    st.caption('''Why can't you upload a photo? Because image hosting is expensive and there are a trillion images on the internet which you can use that are already hosted. 😅 AI generate one and upload it to an image hosting site if you really want a custom image.''')
                    submitted_reward = st.form_submit_button("Save Reward")
    # --- Tab 4: Assign Activities ---
            with tab5:
                st.header("🎯 Assign Activities to Your Child")

                # --- Get Parent's Children ---
                try:
                    parent_config_details = config['credentials']['usernames'][username]
                    parent_children_usernames = parent_config_details.get('children', [])
                except KeyError:
                    st.error("Error: Could not find your configuration details.")
                    parent_children_usernames = []

                if not parent_children_usernames:
                    st.warning("You are not currently assigned any children to manage in the configuration.")
                else:
                    # --- Child Selection ---
                    kid_display_names = {
                        kid_un: config['credentials']['usernames'].get(kid_un, {}).get('name', kid_un)
                        for kid_un in parent_children_usernames if kid_un in config['credentials']['usernames']
                    }
                    if not kid_display_names:
                        st.warning("Assigned children not found in user configuration.")
                    else:
                        selected_kid_display_name = st.selectbox(
                            "1. Select Your Child:",
                            options=[""] + list(kid_display_names.values()),
                            key="assign_select_child"
                        )
                        selected_kid_username = None
                        for un, display_name in kid_display_names.items():
                            if display_name == selected_kid_display_name:
                                selected_kid_username = un
                                break

                        if selected_kid_username: # Only proceed if a child is selected
                            # --- Activity Type Selection ---
                            assign_type = st.radio(
                                "2. Select Type to Assign:",
                                ["Standalone Task", "Quest", "Mission"],
                                horizontal=True,
                                key="assign_type_radio"
                            )

                            # --- Template Selection (Conditional) ---
                            selected_template_id = None
                            template_options = {}

                            if assign_type == "Standalone Task":
                                if not task_templates:
                                    st.warning("No standalone task templates have been created yet.")
                                else:
                                    template_options = {tid: f"{tdata.get('emoji','')} {tdata.get('name', tid)} ({tdata.get('points', tid)} pts) - {tdata.get('description', tid)} ({tid})" for tid, tdata in task_templates.items()}
                                    selected_template_display = st.selectbox(
                                        f"3. Select {assign_type}:",
                                        options=[""] + list(template_options.values()),
                                        key="assign_select_task"
                                    )
                                    for tid, display in template_options.items():
                                        if display == selected_template_display:
                                            selected_template_id = tid
                                            break

                            elif assign_type == "Quest":
                                if not quest_templates:
                                    st.warning("No quest templates have been created yet.")
                                else:
                                    template_options = {qid: f"{qdata.get('emoji','')} {qdata.get('name', qid)} ({qdata.get('quest_combined_points', qid)} pts) - {qdata.get('description', qid)} ({qid})" for qid, qdata in quest_templates.items()}
                                    selected_template_display = st.selectbox(
                                        f"3. Select {assign_type}:",
                                        options=[""] + list(template_options.values()),
                                        key="assign_select_quest"
                                    )
                                    for qid, display in template_options.items():
                                        if display == selected_template_display:
                                            selected_template_id = qid
                                            break

                            elif assign_type == "Mission":
                                if not mission_templates:
                                    st.warning("No mission templates have been created yet.")
                                else:
                                    template_options = {mid: f"{mdata.get('emoji','')} {mdata.get('name', mid)} ({mdata.get('mission_combined_points', mid)} pts) - {mdata.get('description', mid)} ({mid})" for mid, mdata in mission_templates.items()}
                                    selected_template_display = st.selectbox(
                                        f"3. Select {assign_type}:",
                                        options=[""] + list(template_options.values()),
                                        key="assign_select_mission"
                                    )
                                    for mid, display in template_options.items():
                                        if display == selected_template_display:
                                            selected_template_id = mid
                                            break

                            # --- Assign Button ---
                            st.divider()
                            if st.button("Assign Activity", key="assign_button", disabled=(not selected_template_id)):
                                if selected_kid_username and selected_template_id and assign_type:
                                    # Generate assignment ID
                                    type_prefix = assign_type.split()[0].lower() # task, quest, or mission
                                    assignment_id = utils.generate_assignment_id(f"{type_prefix}_{selected_template_id}")

                                    # Prepare base assignment data
                                    new_assignment_data = {
                                        "type": type_prefix,
                                        "template_id": selected_template_id,
                                        "assigned_by": username, # Logged-in parent username
                                        "assigned_on": datetime.now().isoformat(),
                                        "status": "pending_acceptance"
                                    }

                                    # Add type-specific data (task_status for quests)
                                    if type_prefix == "quest":
                                        quest_template_tasks = quest_templates.get(selected_template_id, {}).get('tasks', [])
                                        new_assignment_data["task_status"] = {
                                            task['id']: "pending" for task in quest_template_tasks if 'id' in task
                                        }
                                    elif type_prefix == "mission":
                                        # For missions, initially no instances needed, just link the template
                                        new_assignment_data["quest_instances"] = {}
                                        new_assignment_data["task_instances"] = {}


                                    # --- Save the Assignment ---
                                    # Load fresh data just before saving
                                    current_assignments = utils.load_assignments(ASSIGNED_QUESTS_FILE)
                                    if current_assignments is None:
                                        st.error("Failed to load current assignments before saving.")
                                    else:
                                        # Ensure kid key exists
                                        if selected_kid_username not in current_assignments:
                                            current_assignments[selected_kid_username] = {}

                                        # Add the new assignment
                                        current_assignments[selected_kid_username][assignment_id] = new_assignment_data

                                        # Attempt to save
                                        if utils.save_assignments(current_assignments, ASSIGNED_QUESTS_FILE):
                                            st.session_state['assigned_quests'] = current_assignments # Update session state
                                            #logging logic
                                            try:
                                                if not username:
                                                    st.warning("Could not log assignment event: User Information not found. Please screenshot and tell Andrew.")
                                                else:
                                                    now_utc = datetime.now(timezone.utc)
                                                    timestamp_iso = now_utc.isoformat()
                                                    assignment_event = {
                                                        "timestamp": timestamp_iso,
                                                        "event_type": f"{type_prefix}_assigned",
                                                        "user": username,
                                                        "affected_item": selected_template_id,
                                                        "message": f"{username} assigned new {type_prefix} to {selected_kid_username}",
                                                    }
                                                    
                                                    current_history = []
                                                    if history_file_path.is_file():
                                                        try:
                                                            with open(history_file_path, 'r', encoding='utf-8') as f:
                                                                content = f.read()
                                                                if content:
                                                                    current_history = json.loads(content)
                                                                    if not isinstance(current_history, list):
                                                                        print(f"Warning: History file {history_file_path} was not a list. Resetting for append.")
                                                                        current_history = []
                                                        except json.JSONDecodeError:
                                                            print(f"Warning: History file {history_file_path} was not a list. Resetting for append.")
                                                            current_history = []
                                                        except OSError as e:
                                                            st.warning(f"Could not read history file to log assignment: {e}")
                                                            current_history = None
                                                    if current_history is not None:
                                                        current_history.append(assignment_event)
                                                        try:
                                                            with open(history_file_path, 'w', encoding='utf-8') as f:
                                                                json.dump(current_history, f, indent=4)
                                                            print(f"Logged assignment event for {firstname}, {selected_template_id}.")
                                                        except OSError as e:
                                                            st.warning(f"Could not write history file to log mission creation: {e}")
                                            except Exception as e:
                                                st.warning(f"An error occured while logging assignment to history: {e}")
                                            st.success(f"{assign_type} '{template_options.get(selected_template_id, selected_template_id)}' assigned to {selected_kid_display_name} for acceptance!")
                                            time.sleep(2)
                                            st.rerun()

                                else:
                                    st.warning("Please ensure a child and an activity template are selected.")
                with tab6:
                    if st.session_state.get('role'):
                        st.header("EVENT HISTORY") # Moved header inside the check for consistency

                        # Ensure we have the user's firstname
                        if not firstname:
                            st.warning("Cannot display history: User information not found.")
                        else:
                            try:
                                # Construct the path to the user's history file
                                safe_filename = f"{firstname}_history.json"
                                history_file_path = HISTORY_FOLDER / safe_filename

                                # Check if the history file exists
                                if history_file_path.is_file():
                                    # Read the content of the history file
                                    with open(history_file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()

                                    # Check if the file is empty before trying to parse JSON
                                    if not content:
                                        st.info("No history events recorded yet.")
                                    else:
                                        # Parse the JSON data
                                        history_data = json.loads(content)

                                        # Check if the loaded data is a list (expected format)
                                        if not isinstance(history_data, list):
                                            st.error("History file format is incorrect. Expected a list of events.")
                                            print(f"Error: History file {history_file_path} is not a list.") # Server log
                                        # Check if the list is empty
                                        elif not history_data:
                                            st.info("No history events recorded yet.")
                                        else:
                                            # --- Convert to Pandas DataFrame ---
                                            df_history = pd.DataFrame(history_data)

                                            # --- Optional: Data Cleaning and Formatting ---

                                            # 1. Convert timestamp string to datetime objects (optional but good practice)
                                            #    Errors='coerce' will turn unparseable timestamps into NaT (Not a Time)
                                            if 'timestamp' in df_history.columns:
                                                df_history['timestamp'] = pd.to_datetime(df_history['timestamp'], errors='coerce')

                                            # 2. Sort by timestamp (most recent first)
                                            if 'timestamp' in df_history.columns:
                                                df_history = df_history.sort_values(by='timestamp', ascending=False)

                                            # 3. Select and reorder columns for display (adjust as needed)
                                            #    Include all likely columns; Pandas handles missing ones with NaN/None
                                            display_columns = ['timestamp', 'event_type', 'message', 'affected_item', 'user']
                                            # Filter to keep only columns that actually exist in the DataFrame
                                            existing_columns = [col for col in display_columns if col in df_history.columns]
                                            df_display = df_history[existing_columns]

                                            # --- Display the DataFrame ---
                                            st.dataframe(
                                                df_display,
                                                use_container_width=True, # Make table use full tab width
                                                hide_index=True # Hide the default numerical index
                                                )
                                            # Alternatively, use st.write(df_display) for a static table

                                else:
                                    # File doesn't exist for this user
                                    st.info(f"No history found for user '{firstname}'.")

                            except json.JSONDecodeError:
                                st.error("Failed to read history file: Invalid format.")
                                print(f"Error: JSONDecodeError reading {history_file_path}") # Server log
                            except FileNotFoundError:
                                # This case is handled by the is_file() check above, but good practice
                                st.info(f"No history found for user '{firstname}'.")
                            except OSError as e:
                                st.error(f"An error occurred while accessing history file: {e}")
                                print(f"Error: OSError accessing {history_file_path}: {e}") # Server log
                            except Exception as e:
                                st.error(f"An unexpected error occurred while displaying history: {e}")
                                print(f"Error: Unexpected error displaying history for {firstname}: {e}") # Server log

                                    
# --- KID/ADMIN ---
if st.session_state.get('role') == 'kid' or st.session_state.get('role') == 'admin':
    tab_list = [
    "🗝️ History",
    "🧑🏽‍💻Code",
    ]
    tab1, tab2 = st.tabs(tab_list)
    
    with tab1:
         if st.session_state.get('role'):
            st.header("EVENT HISTORY") # Moved header inside the check for consistency

            # Ensure we have the user's firstname
            if not firstname:
                st.warning("Cannot display history: User information not found.")
            else:
                try:
                    # Construct the path to the user's history file
                    safe_filename = f"{firstname}_history.json"
                    history_file_path = HISTORY_FOLDER / safe_filename

                    # Check if the history file exists
                    if history_file_path.is_file():
                        # Read the content of the history file
                        with open(history_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check if the file is empty before trying to parse JSON
                        if not content:
                            st.info("No history events recorded yet.")
                        else:
                            # Parse the JSON data
                            history_data = json.loads(content)

                            # Check if the loaded data is a list (expected format)
                            if not isinstance(history_data, list):
                                st.error("History file format is incorrect. Expected a list of events.")
                                print(f"Error: History file {history_file_path} is not a list.") # Server log
                            # Check if the list is empty
                            elif not history_data:
                                st.info("No history events recorded yet.")
                            else:
                                # --- Convert to Pandas DataFrame ---
                                df_history = pd.DataFrame(history_data)

                                # --- Optional: Data Cleaning and Formatting ---

                                # 1. Convert timestamp string to datetime objects (optional but good practice)
                                #    Errors='coerce' will turn unparseable timestamps into NaT (Not a Time)
                                if 'timestamp' in df_history.columns:
                                    df_history['timestamp'] = pd.to_datetime(df_history['timestamp'], errors='coerce')

                                # 2. Sort by timestamp (most recent first)
                                if 'timestamp' in df_history.columns:
                                    df_history = df_history.sort_values(by='timestamp', ascending=False)

                                # 3. Select and reorder columns for display (adjust as needed)
                                #    Include all likely columns; Pandas handles missing ones with NaN/None
                                display_columns = ['timestamp', 'event_type', 'message', 'affected_item', 'user']
                                # Filter to keep only columns that actually exist in the DataFrame
                                existing_columns = [col for col in display_columns if col in df_history.columns]
                                df_display = df_history[existing_columns]

                                # --- Display the DataFrame ---
                                st.dataframe(
                                    df_display,
                                    use_container_width=True, # Make table use full tab width
                                    hide_index=True # Hide the default numerical index
                                    )
                                # Alternatively, use st.write(df_display) for a static table

                    else:
                        # File doesn't exist for this user
                        st.info(f"No history found for user '{firstname}'.")

                except json.JSONDecodeError:
                    st.error("Failed to read history file: Invalid format.")
                    print(f"Error: JSONDecodeError reading {history_file_path}") # Server log
                except FileNotFoundError:
                    # This case is handled by the is_file() check above, but good practice
                    st.info(f"No history found for user '{firstname}'.")
                except OSError as e:
                    st.error(f"An error occurred while accessing history file: {e}")
                    print(f"Error: OSError accessing {history_file_path}: {e}") # Server log
                except Exception as e:
                    st.error(f"An unexpected error occurred while displaying history: {e}")
                    print(f"Error: Unexpected error displaying history for {firstname}: {e}") # Server log
    
    with tab2:
        st.header("Hey, how'd you build this? 🤔")
        st.write("Curious how I bulit this web application?")
        st.write("This entire webpage was created by me (yes, WITHOUT the use of AI) - including all of the logic behind the scenes that makes it work.")
        st.markdown(f"You can view all of the code that makes it run on my github by [clicking here.](https://github.com/JAndrewGibson/family-rewards-streamlit)")
        st.write("Here's how this small portion of the website looks in the code:")
        st.code('''           
    if st.session_state.get('role') == 'kid' or st.session_state.get('role') == 'admin':
        st.header("Hey, how'd you build this?")
        st.write("Curious how I bulit this web application?")
        st.write("This entire webpage was created by me (yes, WITHOUT the use of AI) - including all of the logic behind the scenes that makes it work.")
        st.markdown(f"You can view all of the code that makes it run on my github by [clicking here.](https://github.com/JAndrewGibson/family-rewards-streamlit)")
        st.write("Here's how this small portion of the website looks in the code:")         
                ''')
        
        st.write("If I'm just writing text or a link, it's pretty easy.")
        st.write("When it get to programming the logic - it gets a little more complex. But don't worry - there's a mission for learning all that.")