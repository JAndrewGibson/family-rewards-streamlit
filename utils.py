import streamlit as st
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import utils

# --- File Constants (Define them here or pass as arguments) ---
# It's often better to define filenames in the main script or pages
# and pass them to these functions. Let's modify them to accept filenames.
TASKS_TEMPLATE_FILE = 'tasks.json'
QUESTS_TEMPLATE_FILE = 'quests.json'
MISSIONS_TEMPLATE_FILE = 'missions.json'
ASSIGNED_QUESTS_FILE = 'assigned_quests.json'
ASSIGNMENTS_FILE = 'assignments.json'

def load_config(path):
    """Loads the YAML configuration file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Use safe_load to avoid arbitrary code execution
            config_data = yaml.safe_load(f)
            # Handle empty file case
            if config_data is None:
                return {}
            return config_data
    except FileNotFoundError:
        st.error(f"Error: Configuration file not found at '{path}'.")
        return None
    except yaml.YAMLError as e:
        st.error(f"Error parsing configuration file: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred loading config: {e}")
        return None

def save_config(path, data):
    """Saves the data dictionary back to the YAML configuration file."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            # default_flow_style=False gives block style, sort_keys=False preserves order somewhat
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return True
    except PermissionError:
        st.error(f"Error: Permission denied writing to configuration file '{path}'.")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred saving config: {e}")
        return False

@st.dialog("First time welcome!")
def show_first_login(role):
    if role == 'kid':
        st.write("Welcome to your rewards page!")
        if st.button("Done"):
            st.rerun()
        st.stop()
    if role == 'parent':
        st.header("You made it!")
        st.subheader("This message will only appear once, so pay attention...")
        st.write("This is the end of the puzzle! You did it!")
        if st.button("I've read everything. Let's see the prize!"):
            st.rerun()
        st.stop()
    else:
        pass

def check_and_complete_quest_instance(kid_username, assign_id, quest_id, assignments_data, points_data, quest_templates):
    """
    Checks if all tasks in a quest instance are done. If so, marks quest instance completed,
    adds bonus points, and returns True. Otherwise returns False.
    Modifies assignments_data and points_data directly.
    """
    print(f"Checking quest completion for {kid_username}, assign_id={assign_id}, quest_id={quest_id}")
    # TODO: Implement detailed logic
    # 1. Find the quest instance in assignments_data
    # 2. Check if all tasks in its 'task_status' are 'completed'
    # 3. If yes:
    #    a. Update the quest instance's 'status' to 'completed'
    #    b. Get bonus points from quest_templates[quest_id]
    #    c. Add bonus points to points_data[kid_username]
    #    d. Return True (indicating quest completion)
    # 4. If no, return False
    quest_completed = False # Placeholder
    # --- Placeholder Logic ---
    try:
         quest_instance = assignments_data[kid_username][assign_id]['task_status'] # Example access for standalone quest
         # quest_instance = assignments_data[kid_username][mission_assign_id]['quest_instances'][quest_id]['task_status'] # Example access for mission quest
         all_done = all(status == 'completed' for status in quest_instance.values())
         if all_done:
              # Example: Update standalone quest status
              if assignments_data[kid_username][assign_id].get('type') == 'quest':
                   assignments_data[kid_username][assign_id]['status'] = 'completed'
              # Example: Update mission quest instance status (more complex access needed)
              # elif ... : assignments_data[kid_username][mission_assign_id]['quest_instances'][quest_id]['status'] = 'completed'

              bonus = quest_templates.get(quest_id, {}).get('completion_bonus_points', 0)
              points_data[kid_username] = points_data.get(kid_username, 0) + bonus
              print(f"Quest {quest_id} completed! Awarded {bonus} bonus points.")
              quest_completed = True
    except KeyError as e:
        print(f"KeyError during quest completion check: {e}") # Debugging
        st.warning("Could not check quest completion due to data structure issue.")

    return quest_completed

def first_name(name):
    if name == None:
        return None
    else:
        full_name = name.split()
        if full_name:
            return full_name[0]
        return ""

def check_and_complete_mission_instance(kid_username, mission_assign_id, assignments_data, points_data, mission_templates, quest_templates, task_templates):
    """
    Checks if all components (quest instances, task instances) within a mission are done.
    If so, marks mission completed, adds reward points, and returns True. Otherwise returns False.
    Modifies assignments_data and points_data directly.
    """
    print(f"Checking mission completion for {kid_username}, mission_assign_id={mission_assign_id}")
    # TODO: Implement detailed logic
    # 1. Find the mission assignment in assignments_data
    # 2. Check status of ALL 'quest_instances' and 'task_instances' within it.
    # 3. If ALL are 'completed':
    #    a. Update mission assignment 'status' to 'completed'
    #    b. Get reward points from mission_templates
    #    c. Add points to points_data
    #    d. Return True
    # 4. If no, return False
    mission_completed = False # Placeholder
    # --- Placeholder Logic ---
    try:
         mission_assignment = assignments_data[kid_username][mission_assign_id]
         all_quests_done = all(inst.get('status') == 'completed' for inst in mission_assignment.get('quest_instances', {}).values())
         all_tasks_done = all(inst.get('status') == 'completed' for inst in mission_assignment.get('task_instances', {}).values())

         if all_quests_done and all_tasks_done:
              mission_assignment['status'] = 'completed'
              mission_template_id = mission_assignment.get('template_id')
              reward = mission_templates.get(mission_template_id, {}).get('completion_reward', {})
              points = reward.get('points', 0)
              points_data[kid_username] = points_data.get(kid_username, 0) + points
              print(f"Mission {mission_template_id} completed! Awarded {points} reward points.")
              mission_completed = True
    except KeyError as e:
         print(f"KeyError during mission completion check: {e}")
         st.warning("Could not check mission completion due to data structure issue.")

    return mission_completed

def update_prerequisites(kid_username, mission_assign_id, assignments_data, mission_templates):
    """
    Recalculates status for items within a mission based on current completion state.
    Updates 'locked' items to 'active' if prerequisites are now met.
    Modifies assignments_data directly. Returns True if any status changed.
    """
    print(f"Updating prerequisites for {kid_username}, mission_assign_id={mission_assign_id}")
    status_changed = False
    # TODO: Implement detailed logic
    # 1. Find the mission assignment and template
    # 2. Loop through all quest_instances and task_instances within the assignment
    # 3. For items currently 'locked':
    #    a. Call calculate_item_status(...) for them
    #    b. If the new status is 'active', update the status in assignments_data and set status_changed = True
    # 4. Return status_changed

    # --- Placeholder Logic ---
    try:
         mission_assignment = assignments_data[kid_username][mission_assign_id]
         mission_template_id = mission_assignment.get('template_id')
         mission_template = mission_templates.get(mission_template_id)
         if not mission_template: return False

         instances_to_check = [
             ('quest', q_id, data) for q_id, data in mission_assignment.get('quest_instances', {}).items()
         ] + [
             ('task', t_id, data) for t_id, data in mission_assignment.get('task_instances', {}).items()
         ]

         for item_type, item_id, instance_data in instances_to_check:
             if instance_data.get('status') == 'locked':
                 new_status = calculate_item_status(item_id, item_type, mission_template, mission_assignment)
                 if new_status == 'active':
                     instance_data['status'] = 'active' # Update status directly in the dict
                     print(f"Item {item_id} unlocked!")
                     status_changed = True
    except KeyError as e:
         print(f"KeyError during prerequisite update check: {e}")
         st.warning("Could not update prerequisites due to data structure issue.")

    return status_changed

def load_points(filename):
    """Loads points data from the JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            points_data = json.load(f)
    except FileNotFoundError:
        points_data = {} # Start empty if file doesn't exist
        try: # Attempt to create the file
            save_points({}, filename)
            st.info(f"Created empty points file: {filename}")
        except Exception as e:
             st.warning(f"Could not create {filename}. Error: {e}")
    except json.JSONDecodeError:
        st.error(f"❌ **Error:** Could not parse points file `{filename}`.")
        points_data = None
    except Exception as e:
        st.error(f"❌ **An unexpected error occurred loading points:** {e}")
        points_data = None
    return points_data

def save_points(data, filename):
    """Saves points data to the JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        st.error(f"❌ Error saving points to `{filename}`: Check permissions. Details: {e}")
        return False
    except Exception as e:
        st.error(f"❌ An unexpected error occurred saving points: {e}")
        return False

def calculate_item_status(item_id, item_type, mission_template, mission_assignment_data):
    """
    Calculates the status (locked, active, completed) of a quest or task instance
    within a specific mission assignment, based on prerequisites.

    Args:
        item_id (str): The template_id of the quest or task item.
        item_type (str): 'quest' or 'task'.
        mission_template (dict): The template data for the parent mission.
        mission_assignment_data (dict): The assignment data for the parent mission instance.

    Returns:
        str: 'locked', 'active', or 'completed'.
    """
    # 1. Check if the item instance itself is already completed
    instance_dict_key = 'quest_instances' if item_type == 'quest' else 'task_instances'
    item_instance = mission_assignment_data.get(instance_dict_key, {}).get(item_id)

    if item_instance and item_instance.get('status') == 'completed':
        return 'completed'

    # 2. Get prerequisites from the mission template
    prerequisites = mission_template.get('prerequisites', {}).get(item_id, [])

    # 3. If no prerequisites, it's active (unless already completed above)
    if not prerequisites:
        return 'active'

    # 4. Check if all prerequisites are met (completed) within this assignment
    all_prereqs_met = True
    for prereq_id in prerequisites:
        # Check both quest and task instances within the current mission assignment
        prereq_quest_instance = mission_assignment_data.get('quest_instances', {}).get(prereq_id)
        prereq_task_instance = mission_assignment_data.get('task_instances', {}).get(prereq_id)

        prereq_completed = False
        if prereq_quest_instance and prereq_quest_instance.get('status') == 'completed':
            prereq_completed = True
        elif prereq_task_instance and prereq_task_instance.get('status') == 'completed':
            prereq_completed = True

        if not prereq_completed:
            all_prereqs_met = False
            break # No need to check further if one prerequisite is not met

    # 5. Return status based on prerequisite check
    if all_prereqs_met:
        return 'active'
    else:
        return 'locked'

def get_item_display_name(item_id, q_templates, t_templates):
    """Gets a display name for a quest or task ID."""
    if item_id in q_templates:
        return f"Quest: {q_templates[item_id].get('name', item_id)}"
    elif item_id in t_templates:
        # Use description for tasks as they might not have a 'name'
        return f"Task: {t_templates[item_id].get('name', item_id)}"
    else:
        return item_id # Fallback to ID if not found

# --- Task Template Functions ---
def load_task_templates(filename):
    """Loads standalone task definitions from the JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        return templates
    except FileNotFoundError:
        st.info(f"Task template file `{filename}` not found. Starting empty.")
        return {} # Start empty if file doesn't exist
    except json.JSONDecodeError:
        st.error(f"❌ **Error:** Could not parse `{filename}`. Check JSON validity.")
        return None # Return None on critical error
    except Exception as e:
        st.error(f"❌ **An unexpected error occurred loading task templates:** {e}")
        return None

def save_task_templates(data, filename):
    """Saves standalone task definitions to the JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        st.error(f"❌ Error saving to `{filename}`: Check permissions. Details: {e}")
        return False
    except Exception as e:
        st.error(f"❌ An unexpected error occurred saving task templates: {e}")
        return False

def display_duties(
    duties_dict: dict,
    duty_templates: dict,
    current_user_id: str,
    assignments_file_path: str,
    history_file_path: str,
    section_title: str,
    empty_message: str,
    show_buttons: str = None, # 'accept_decline', 'complete', 'awaiting', 'completed', 'declined'
    duty_type_singular: str = "Duty", # e.g., "Task", "Quest"
    # duty_type_plural: str = "Duties" # e.g., "Tasks", "Quests" - can be derived if needed
):
    """
    Displays a collection of duties (tasks, quests, etc.) in a structured layout.

    Args:
        duties_dict: Dictionary of assignments for the current section (e.g., pending_tasks).
        duty_templates: Dictionary of all available templates (e.g., task_templates, quest_templates).
        current_user_id: The username of the child currently interacting.
        assignments_file_path: Path to the assignments.json file.
        history_file_path: Path to the history_log.json file.
        section_title: Title for this section of duties.
        empty_message: Message to display if duties_dict is empty.
        show_buttons: Controls which buttons are displayed ('accept_decline', 'complete', 'awaiting', 'completed', 'declined').
        duty_type_singular: The singular name for the type of duty being displayed (e.g., "Task", "Quest").
    """
    st.subheader(section_title)
    if not duties_dict:
        st.info(empty_message)
        return

    with st.container(border=True):
        num_duties = len(duties_dict)
        max_cols = 3
        num_cols = min(num_duties, max_cols)
        cols = st.columns(num_cols)
        col_idx = 0

        for assign_id, assign_data in duties_dict.items():
            # Determine the ID of the task/quest template
            # Prioritize specific IDs, then fall back to a generic 'template_id'
            template_id = assign_data.get(f"{duty_type_singular.lower()}_id") or \
                          assign_data.get('template_id') or \
                          assign_data.get('task_id') # Keep task_id as a common fallback

            duty_template = duty_templates.get(template_id)

            if not duty_template:
                st.warning(
                    f"{duty_type_singular} template '{template_id}' not found for assignment '{assign_id}'. Skipping."
                )
                continue

            duty_name = duty_template.get('name', f'Unnamed {duty_type_singular}')
            duty_emoji = duty_template.get('emoji', '❓')
            duty_description = duty_template.get('description', 'No description.')
            duty_points = duty_template.get('points', 0)

            with cols[col_idx % num_cols]:
                with st.container(border=True):
                    st.subheader(f"{duty_emoji} {duty_name}")
                    st.caption(duty_description)
                    st.markdown(f"**Points:** {duty_points:,}")

                    # --- Action Buttons ---
                    button_key_prefix = f"{show_buttons}_{duty_type_singular.lower()}_{assign_id}"

                    if show_buttons == 'accept_decline':
                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if st.button("✅ Accept", key=f"accept_{button_key_prefix}", use_container_width=True):
                                current_assignments_state = st.session_state.get("assignments", {})
                                if current_user_id in current_assignments_state and \
                                   assign_id in current_assignments_state[current_user_id]:
                                    current_assignments_state[current_user_id][assign_id]['status'] = 'active'
                                    if save_assignments(current_assignments_state, assignments_file_path):
                                        st.success(f"{duty_type_singular} '{duty_name}' accepted!")
                                        log_into_history(
                                            event_type=f"{duty_type_singular.lower()}_accepted",
                                            message=f"User '{current_user_id}' accepted {duty_type_singular.lower()} '{duty_name}' (ID: {assign_id})",
                                            affected_item=assign_id,
                                            username=current_user_id,
                                            history_file_path=history_file_path
                                        )
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to save acceptance for {duty_type_singular.lower()}.")
                                else:
                                    st.error(f"Assignment '{assign_id}' not found for user '{current_user_id}'. Please refresh.")
                                    # Potentially st.rerun() or just let the user see the error
                        with b_col2:
                            if st.button("❌ Decline", key=f"decline_{button_key_prefix}", use_container_width=True):
                                current_assignments_state = st.session_state.get("assignments", {})
                                if current_user_id in current_assignments_state and \
                                   assign_id in current_assignments_state[current_user_id]:
                                    current_assignments_state[current_user_id][assign_id]['status'] = 'declined'
                                    if save_assignments(current_assignments_state, assignments_file_path):
                                        st.warning(f"{duty_type_singular} '{duty_name}' declined.")
                                        log_into_history(
                                            event_type=f"{duty_type_singular.lower()}_declined",
                                            message=f"User '{current_user_id}' declined {duty_type_singular.lower()} '{duty_name}' (ID: {assign_id})",
                                            affected_item=assign_id,
                                            username=current_user_id,
                                            history_file_path=history_file_path
                                        )
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to save decline for {duty_type_singular.lower()}.")
                                else:
                                    st.error(f"Assignment '{assign_id}' not found for user '{current_user_id}'. Please refresh.")

                    elif show_buttons == 'complete':
                        if st.button(f"🏁 Mark as Complete", key=f"complete_{button_key_prefix}", use_container_width=True):
                            current_assignments_state = st.session_state.get("assignments", {})
                            if current_user_id in current_assignments_state and \
                               assign_id in current_assignments_state[current_user_id]:
                                current_assignments_state[current_user_id][assign_id]['status'] = 'awaiting approval'
                                if save_assignments(current_assignments_state, assignments_file_path):
                                    st.success(f"{duty_type_singular} '{duty_name}' submitted for approval!")
                                    st.balloons()
                                    log_into_history(
                                        event_type=f"{duty_type_singular.lower()}_submitted",
                                        message=f"User '{current_user_id}' submitted {duty_type_singular.lower()} '{duty_name}' (ID: {assign_id}) for approval",
                                        affected_item=assign_id,
                                        username=current_user_id,
                                        history_file_path=history_file_path
                                    )
                                    st.rerun()
                                else:
                                    st.error(f"Failed to submit {duty_type_singular.lower()} for approval.")
                            else:
                                st.error(f"Assignment '{assign_id}' not found for user '{current_user_id}'. Please refresh.")

                    elif show_buttons == 'awaiting':
                        st.info("⏳ Awaiting Parent Approval")

                    elif show_buttons == 'completed':
                        st.success("✅ Completed!")
                        completed_timestamp = assign_data.get('completed_timestamp')
                        if completed_timestamp:
                            try:
                                # Example: Assuming ISO format timestamp
                                completed_dt = datetime.datetime.fromisoformat(str(completed_timestamp))
                                st.caption(f"Completed on: {completed_dt.strftime('%Y-%m-%d %H:%M')}")
                            except ValueError:
                                st.caption(f"Completed: {completed_timestamp}") # Show raw if parsing fails

                    elif show_buttons == 'declined':
                        st.error("❌ Declined")
                        # You might want to show a reason or timestamp if available
                        declined_timestamp = assign_data.get('declined_timestamp') # If you store this
                        if declined_timestamp:
                             st.caption(f"Declined on: {declined_timestamp}")


                col_idx += 1

def display_tasks(task_dict, section_title, empty_message, show_buttons=None):
    task_templates = st.session_state.get("task_templates")
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
                    st.markdown(f"**Points:** {task_template.get('points', 0):,}")

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
                                            event_type="standalone_submitted",
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
                            st.error("❌ Declined")

            col_index += 1

# --- Quest Template Functions (Assumed Existing from previous examples) ---
def load_quest_templates(filename):
    # ... (keep existing implementation, ensure it returns {} or None on error) ...
    # Example from before:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        return templates
    except FileNotFoundError:
        st.info(f"Quest template file `{filename}` not found. Starting empty.")
        return {}
    except json.JSONDecodeError:
        st.error(f"❌ **Error:** Could not parse `{filename}`. Check JSON validity.")
        return None
    except Exception as e:
        st.error(f"❌ **An unexpected error occurred loading quest templates:** {e}")
        return None

def save_quest_templates(data, filename):
    """Saves quest definitions to the JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        st.error(f"❌ Error saving to `{filename}`: Check permissions. Details: {e}")
        return False
    except Exception as e:
        st.error(f"❌ An unexpected error occurred saving quest templates: {e}")
        return False

# --- Mission Template Functions ---
def load_mission_templates(filename):
    """Loads mission definitions from the JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        return templates
    except FileNotFoundError:
        st.info(f"Mission template file `{filename}` not found. Starting empty.")
        return {}
    except json.JSONDecodeError:
        st.error(f"❌ **Error:** Could not parse `{filename}`. Check JSON validity.")
        return None
    except Exception as e:
        st.error(f"❌ **An unexpected error occurred loading mission templates:** {e}")
        return None

def save_mission_templates(data, filename):
    """Saves mission definitions to the JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        st.error(f"❌ Error saving to `{filename}`: Check permissions. Details: {e}")
        return False
    except Exception as e:
        st.error(f"❌ An unexpected error occurred saving mission templates: {e}")
        return False

# --- Assigned Quest Functions ---
def load_assignments(filename): # Renamed function
    """Loads assignment data (missions, quests, tasks) from the JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            assigned = json.load(f)
    except FileNotFoundError:
        assigned = {}
        try:
            save_assignments({}, filename) # Create the file with empty data
            st.info(f"Created empty assignments file: {filename}")
        except Exception as e:
             st.warning(f"Could not automatically create {filename}. Needs write permission. Error: {e}")
    except json.JSONDecodeError:
        st.error(f"❌ **Error:** Could not parse assignment file `{filename}`.")
        assigned = None # Return None on critical parse error
    except Exception as e:
         st.error(f"❌ **An unexpected error occurred loading assignments:** {e}")
         assigned = None
    return assigned

def save_assignments(data, filename): # Renamed function
    """Saves assignment data (missions, quests, tasks) to the JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        st.error(f"❌ Error saving assignments to `{filename}`: Check permissions. Details: {e}")
        return False
    except Exception as e:
        st.error(f"❌ An unexpected error occurred saving assignments: {e}")
        return False

def generate_assignment_id(quest_id):
    """Generates a unique ID for a quest assignment."""
    timestamp = int(time.time())
    short_quest_id = quest_id.replace("quest_", "")[:10]
    return f"assign_{timestamp}_{short_quest_id}"

def log_into_history(event_type, message, affected_item, username):
    safe_filename = f"{username}_history.json"
    HISTORY_FOLDER = Path("user_history")
    HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)
    history_file_path = HISTORY_FOLDER / safe_filename
    try:
        if not username:
            st.warning("Could not log assignment event: User Information not found. Please screenshot and tell Andrew.")
        else:
            now_utc = datetime.now(timezone.utc)
            timestamp_iso = now_utc.isoformat()
            assignment_event = {
                "timestamp": timestamp_iso,
                "event_type": event_type,
                "user": username,
                "affected_item": affected_item,
                "message": message,
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
            else:
                st.error("History file not found!")
            if current_history is not None:
                current_history.append(assignment_event)
                try:
                    with open(history_file_path, 'w', encoding='utf-8') as f:
                        json.dump(current_history, f, indent=4)
                        return True
                except OSError as e:
                    st.warning(f"Could not write history file to log mission creation: {e}")
            else:
                st.error("Current history is none.")
    except Exception as e:
        st.warning(f"An error occured while logging assignment to history: {e}")