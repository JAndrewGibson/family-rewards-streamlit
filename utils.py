# utils.py

import streamlit as st
import json
import time

# --- File Constants (Define them here or pass as arguments) ---
# It's often better to define filenames in the main script or pages
# and pass them to these functions. Let's modify them to accept filenames.
TASKS_TEMPLATE_FILE = 'tasks.json'
QUESTS_TEMPLATE_FILE = 'quests.json'
MISSIONS_TEMPLATE_FILE = 'missions.json'
ASSIGNED_QUESTS_FILE = 'assigned_quests.json'

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
        return f"Task: {t_templates[item_id].get('description', item_id)}"
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