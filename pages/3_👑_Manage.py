import streamlit as st
import utils # Import shared utility functions
import datetime
import time # For assignment ID generation

# --- Page Configuration ---
st.set_page_config(page_title="Manage & Assign", page_icon="👑")
st.title("👑 Content Management & Assignment")

# --- Authentication & Authorization Check ---
# Ensure user is logged in AND is a parent
if st.session_state.get('authentication_status') is not True or st.session_state.get('role') != 'parent':
    st.warning("🔒 You must be logged in as a Parent to access this page.")
    st.stop() # Do not render anything else

# --- Constants for filenames ---
TASKS_TEMPLATE_FILE = 'tasks.json'
QUESTS_TEMPLATE_FILE = 'quests.json'
MISSIONS_TEMPLATE_FILE = 'missions.json'
ASSIGNED_QUESTS_FILE = 'assignments.json'

# --- Load Data (Load fresh for management/assignment actions) ---
# Use .get() from session state for config, but load templates/assignments fresh
config = st.session_state.get("config")
username = st.session_state.get("username") # Logged-in parent's username

if not config or not username:
     st.error("User configuration not found in session state. Please log in again.")
     st.stop()

# --- Load Existing Templates (Load fresh each time or use session state carefully) ---
task_templates = utils.load_task_templates(TASKS_TEMPLATE_FILE)
quest_templates = utils.load_quest_templates(QUESTS_TEMPLATE_FILE)
mission_templates = utils.load_mission_templates(MISSIONS_TEMPLATE_FILE)
# Load assignments fresh before potential modification
assignments_data = utils.load_assignments(ASSIGNED_QUESTS_FILE)

def get_item_display_name(item_id, q_templates, t_templates):
    """Gets a display name for a quest or task ID."""
    quest_info = q_templates.get(item_id)
    if quest_info:
        return f"Quest: {quest_info.get('name', item_id)}"
    task_info = t_templates.get(item_id)
    if task_info:
        return f"Task: {task_info.get('description', item_id)}"
    return item_id # Fallback

# Handle loading errors
if task_templates is None or quest_templates is None or mission_templates is None or assignments_data is None:
    st.error("Failed to load one or more data files. Cannot proceed.")
    st.stop()

# --- Define Tabs ---
tab_list = [
    "📝 Manage Tasks",
    "⚔️ Manage Quests",
    "🗺️ Manage Missions",
    "🎯 Assign Activities" # New Tab
]
tab1, tab2, tab3, tab4 = st.tabs(tab_list)

# --- Manage Tasks Tab ---
with tab1:
    st.header("📝 Standalone Task Templates")
    st.write("Define reusable individual tasks.")

    # Display existing tasks (optional enhancement)
    with st.expander("View Existing Task Templates"):
        if not task_templates:
            st.info("No standalone task templates defined yet.")
        else:
            for task_id, task_data in task_templates.items():
                st.write(f"- **{task_id}**: {task_data.get('emoji','')} {task_data.get('description','')} ({task_data.get('points',0)} pts)")

    st.divider()
    st.subheader("Create New Task Template")

    # Use a form for better state management on creation
    with st.form("new_task_form", clear_on_submit=True):
        new_task_id = st.text_input("Task ID (unique, e.g., 'task_clean_dishes'):")
        new_task_desc = st.text_area("Description:")
        new_task_points = st.number_input("Points:", min_value=0, step=1, value=10)
        new_task_emoji = st.text_input("Emoji Icon:", max_chars=2)

        submitted_task = st.form_submit_button("Save Task Template")
        if submitted_task:
            # Validation
            if not new_task_id:
                st.error("Task ID cannot be empty.")
            elif not new_task_desc:
                st.error("Task description cannot be empty.")
            elif new_task_id in task_templates:
                st.error(f"Task ID '{new_task_id}' already exists. Please choose a unique ID.")
            else:
                # Add to data structure
                task_templates[new_task_id] = {
                    "description": new_task_desc,
                    "points": new_task_points,
                    "emoji": new_task_emoji
                }
                # Attempt to save
                if utils.save_task_templates(task_templates, TASKS_TEMPLATE_FILE):
                    st.success(f"Task template '{new_task_id}' saved successfully!")
                    # No rerun needed due to clear_on_submit=True and reloading data next time
                else:
                    # Error message handled by save function, remove potentially corrupt data
                    del task_templates[new_task_id] # Roll back change if save failed

# --- Tab 2: Manage Quests ---
with tab2:
    st.header("⚔️ Quest Templates")
    st.write("Define quests composed of multiple steps (tasks defined within).")

    with st.expander("View Existing Quest Templates"):
         if not quest_templates:
            st.info("No quest templates defined yet.")
         else:
            for quest_id, quest_data in quest_templates.items():
                 col1, col2 = st.columns([3,1])
                 with col1:
                    st.write(f"**{quest_id}**: {quest_data.get('emoji','')} {quest_data.get('name','')}")
                 # Add delete button functionality here later if needed

    st.divider()
    st.subheader("Create or Edit Quest Template") # Changed subheader slightly

    # Initialize session state list for tasks in the current quest being built/edited
    if 'current_quest_tasks' not in st.session_state:
        st.session_state.current_quest_tasks = []

    # Optional: Add selectbox to load existing quest for editing (more complex state)
    # Simple approach: Focus on creation first. Clear state for new quest.
    # if st.button("Start New Quest Definition"):
    #     st.session_state.current_quest_tasks = []
    #     # Clear other potential form states if needed

    with st.form("new_quest_form"): # Don't clear on submit automatically
        st.write("**Quest Details:**")
        new_quest_id = st.text_input("Quest ID (unique, e.g., 'quest_yard_work'):", key="quest_form_id")
        new_quest_name = st.text_input("Quest Name:", key="quest_form_name")
        new_quest_desc = st.text_area("Description:", key="quest_form_desc")
        new_quest_emoji = st.text_input("Emoji Icon:", max_chars=2, key="quest_form_emoji")
        new_quest_bonus = st.number_input("Completion Bonus Points:", min_value=0, step=5, value=0, key="quest_form_bonus")

        st.divider()
        st.write("**Tasks within this Quest:**")

        # Display input fields for tasks currently in session state
        tasks_to_render = st.session_state.current_quest_tasks
        for i, task_data in enumerate(tasks_to_render):
            st.markdown(f"--- *Task Step {i+1}* ---")
            cols = st.columns([2, 4, 1, 1]) # Adjust ratios as needed
            # Use default values from session state for potential pre-filling
            task_data['id'] = cols[0].text_input(f"Task ID (unique within quest)", value=task_data.get('id',''), key=f"q_task_id_{i}")
            task_data['description'] = cols[1].text_area(f"Task Description", value=task_data.get('description',''), key=f"q_task_desc_{i}")
            task_data['points'] = cols[2].number_input(f"Pts", min_value=0, step=1, value=task_data.get('points',0), key=f"q_task_points_{i}")
            task_data['emoji'] = cols[3].text_input(f"Emoji", value=task_data.get('emoji',''), max_chars=2, key=f"q_task_emoji_{i}")
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
                task_desc = st.session_state.get(f"q_task_desc_{i}", "").strip()
                task_points = st.session_state.get(f"q_task_points_{i}", 0)
                task_emoji = st.session_state.get(f"q_task_emoji_{i}", "")

                # Basic validation for each task step
                if not task_id:
                    st.error(f"Task Step {i+1}: ID cannot be empty.")
                    valid_tasks = False
                if not task_desc:
                     st.error(f"Task Step {i+1}: Description cannot be empty.")
                     valid_tasks = False
                # Add check for unique task IDs within this quest? (Advanced)

                final_tasks.append({
                    "id": task_id,
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
                     "tasks": final_tasks, # Use the reconstructed list
                     "completion_bonus_points": st.session_state.quest_form_bonus
                 }
                 if utils.save_quest_templates(quest_templates, QUESTS_TEMPLATE_FILE):
                     st.success(f"Quest template '{quest_id}' saved successfully!")
                     # Clear the task list in session state for the next creation
                     st.session_state.current_quest_tasks = []
                     # We might need to rerun to clear the main form fields if clear_on_submit isn't working as expected
                     # st.experimental_rerun() # Use if form fields don't clear properly
                 else:
                     # Save failed, roll back
                     del quest_templates[quest_id]
                     st.error("Saving failed. Please check permissions or logs.")

    # --- "Add Task Step" Button (Outside the form) ---
    if st.button("➕ Add Task Step to Quest Definition"):
        # Add a new blank task structure to the list in session state
        st.session_state.current_quest_tasks.append({"id": "", "description": "", "points": 0, "emoji": ""})
        st.rerun()
        # No rerun needed here, Streamlit will rerun when the button state changes,
        # and the form will re-render with the new item from session state.

# --- Tab 3: Manage Missions ---
with tab3:
    st.header("🗺️ Mission Templates")
    st.write("Define large goals containing Quests and/or standalone Tasks.")

    with st.expander("View Existing Mission Templates"):
        # ... (Existing code to view missions) ...
        pass # Placeholder

    st.divider()
    st.subheader("Create New Mission Template")

    # Use a single form for the entire mission creation including prerequisites
    with st.form("new_mission_form", clear_on_submit=False):
        new_mission_id = st.text_input("Mission ID (unique, e.g., 'mission_summer_reading'):")
        new_mission_name = st.text_input("Mission Name:")
        new_mission_desc = st.text_area("Description:")
        new_mission_emoji = st.text_input("Emoji Icon:", max_chars=2)
        st.divider()

        # --- Select Contained Items ---
        st.markdown("**Select Components for this Mission:**")
        quest_options_map = {qid: get_item_display_name(qid, quest_templates, task_templates) for qid in quest_templates}
        selected_quest_ids = st.multiselect(
            "Include Quests:",
            options=list(quest_options_map.keys()),
            format_func=lambda qid: quest_options_map[qid],
            key="mission_quests_select" # Assign a key
        )

        task_options_map = {tid: get_item_display_name(tid, quest_templates, task_templates) for tid in task_templates}
        selected_task_ids = st.multiselect(
            "Include Standalone Tasks:",
            options=list(task_options_map.keys()),
            format_func=lambda tid: task_options_map[tid],
            key="mission_tasks_select" # Assign a key
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
        completion_points = st.number_input("Completion Points Reward:", min_value=0, step=10, value=0)
        completion_desc = st.text_input("Other Reward Description (optional):")

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


             # Assume basic validation passed... (add your checks here)
             valid_to_save = True
             if not mission_id or not mission_name:
                 st.error("Mission ID and Name cannot be empty.")
                 valid_to_save = False
             elif mission_id in mission_templates:
                  st.error(f"Mission ID '{mission_id}' already exists.")
                  valid_to_save = False
             # Add other validation...

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
                     "completion_reward": {"points": completion_points, "description": completion_desc }
                  }

                  # --- Save ---
                  if utils.save_mission_templates(mission_templates, MISSIONS_TEMPLATE_FILE):
                      st.success(f"Mission template '{mission_id}' saved successfully!")

                      # --- !!! MANUALLY CLEAR FORM WIDGET STATES !!! ---
                      # Clear basic text/number inputs
                      st.session_state.new_mission_id = ""
                      st.session_state.new_mission_name = ""
                      st.session_state.new_mission_desc = ""
                      st.session_state.new_mission_emoji = ""
                      st.session_state.completion_points = 0
                      st.session_state.completion_desc = ""
                      # Clear multiselects
                      st.session_state.mission_quests_select = []
                      st.session_state.mission_tasks_select = []
                      # Clear dynamic prerequisite multiselects
                      for item_id in final_all_selected:
                           prereq_key = f"prereq_{item_id}"
                           if prereq_key in st.session_state:
                               st.session_state[prereq_key] = []
                      # --- End Manual Clear ---

                      st.experimental_rerun() # Rerun AFTER clearing state

                  else:
                      # Save failed, roll back if needed
                      if mission_id in mission_templates: del mission_templates[mission_id]
                      # Error message is shown by save function
                     
# --- Tab 4: Assign Activities ---
with tab4:
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
                         template_options = {tid: f"{tdata.get('emoji','')} {tdata.get('description', tid)} ({tid})" for tid, tdata in task_templates.items()}
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
                        template_options = {qid: f"{qdata.get('emoji','')} {qdata.get('name', qid)} ({qid})" for qid, qdata in quest_templates.items()}
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
                        template_options = {mid: f"{mdata.get('emoji','')} {mdata.get('name', mid)} ({mid})" for mid, mdata in mission_templates.items()}
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
                            "assigned_on": datetime.datetime.now().isoformat(),
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
                                st.success(f"{assign_type} '{template_options.get(selected_template_id, selected_template_id)}' assigned to {selected_kid_display_name} for acceptance!")
                                # Consider if a rerun is needed or if form clearing is sufficient
                                # st.experimental_rerun() # Might cause selections to reset abruptly
                            # Error is handled by save function

                    else:
                        st.warning("Please ensure a child and an activity template are selected.")