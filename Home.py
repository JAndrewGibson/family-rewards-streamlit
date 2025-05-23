import streamlit as st
import auth
import utils
from datetime import datetime, timezone
import time
from pathlib import Path
import json
import os

st.set_page_config(page_title="Explorers", page_icon="😎", layout="wide",menu_items={
           "Get help": "https://www.example.com",  # Add a custom menu item
           "About" : '''
           Can you believe it? I started building this website months ago. My tracker places development time around 450 hours.
           '''
       })


hide_menu_style = """
    <style>
    .st-emotion-cache-15yi2hn.eecegii10 [data-testid="stMarkdownContainer"] p:last-child {
  display: none !important;
}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)

with st.spinner("Loading authentication", show_time=True):
    name, authentication_status, username = auth.authenticate()

if authentication_status is False:
    st.error('Username/password is incorrect')
    if 'login_event_logged' in st.session_state:
        del st.session_state['login_event_logged']
    st.stop()
elif authentication_status is None:
    if 'login_event_logged' in st.session_state:
        del st.session_state['login_event_logged']
    st.stop()

with st.spinner("Getting all the goodies together...", show_time=True):
    # --- Configuration and Constants ---
    TASKS_TEMPLATE_FILE = 'tasks.json'
    QUESTS_TEMPLATE_FILE = 'quests.json'
    MISSIONS_TEMPLATE_FILE = 'missions.json'
    ASSIGNMENTS_FILE = 'assignments.json'
    POINTS_FILE = 'points.json'
    HISTORY_FOLDER = Path("user_history")
    
    # --- Load Data into Session State After Login (If not already loaded) ---
    if authentication_status:
        if 'quest_templates' not in st.session_state:
            st.session_state['quest_templates'] = utils.load_quest_templates(QUESTS_TEMPLATE_FILE)
        if 'assignments' not in st.session_state:
            st.session_state['assignments'] = utils.load_assignments(ASSIGNMENTS_FILE)
        if 'task_templates' not in st.session_state:
            st.session_state['task_templates'] = utils.load_task_templates(TASKS_TEMPLATE_FILE)
        if 'mission_templates' not in st.session_state:
            st.session_state['mission_templates'] = utils.load_mission_templates(MISSIONS_TEMPLATE_FILE)
        if 'points' not in st.session_state:
            st.session_state['points'] = utils.load_points(POINTS_FILE)
        if 'config' not in st.session_state:
            st.session_state['config'] = auth.load_config()
        if 'points' not in st.session_state:
            st.session_state['points'] = utils.load_points(POINTS_FILE)
        if 'username' not in st.session_state:
            st.session_state['username'] = username
        if 'name' not in st.session_state:
            st.session_state['name'] = name
        if 'birthday' not in st.session_state:
            st.session_state['birthday'] = st.session_state.get('birthday', {}).get(username, 0)
        
        if st.session_state.get('assignments') is None or \
        st.session_state.get('task_templates') is None or \
        st.session_state.get('quest_templates') is None or \
        st.session_state.get('mission_templates') is None or \
        st.session_state.get('points') is None:
            st.error("CRITICAL ERROR: Failed to load essential data files after login.")
            st.stop()


    # Get all states AFTER they're loaded into the session state.
    config = st.session_state.get('config')
    points_data = st.session_state.get('points')
    assignments_data = st.session_state.get('assignments')
    mission_templates = st.session_state.get("mission_templates")
    quest_templates = st.session_state.get("quest_templates")
    task_templates = st.session_state.get("task_templates")
    current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
    current_points = f"{current_points_unformatted:,}"
    firstname = utils.first_name(name)
    user_config_details = config.get('credentials',{}).get('usernames',{}).get(username,{})
    user_timezone = user_config_details.get('timezone', [])

# --- LOGGED IN STATE ---

    

    # --- Check if login event has already been logged for this session ---
    if not st.session_state.get('login_event_logged', False):
        try:
            HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)
            safe_filename = f"{username}_history.json" # Use a safe version of the name if needed
            print(f"Safe filename: {safe_filename}")
            history_file_path = HISTORY_FOLDER / safe_filename

            # --- Create history file if it doesn't exist ---
            if not history_file_path.is_file():
                initial_history_data = []
                try:
                    with open(history_file_path, 'w', encoding='utf-8') as f:
                        json.dump(initial_history_data, f, indent=4)
                    print(f"Created history file for {firstname} at: {history_file_path}") # Log for debugging
                    utils.show_first_login(st.session_state.get('role'))
                except OSError as e:
                    st.error(f"Failed to create history file: {e}")
                    st.stop()

            # --- Log the event of user login (only if not already logged this session) ---
            now_utc = datetime.now(timezone.utc)
            timestamp_iso = now_utc.isoformat() # Standard ISO 8601 format

            login_event = {
                "timestamp": timestamp_iso,
                "event_type": "login",
                "user": username,
                "message": f"{username} logged in.",
                "affected_item":f"{username}"
            }

            # --- Read, Append, Write ---
            current_history = []
            try:
                # Read existing data (even if file was just created, it's empty list)
                with open(history_file_path, 'r', encoding='utf-8') as f:
                    # Handle empty file case gracefully before JSON decoding
                    content = f.read()
                    if content:
                        current_history = json.loads(content)
                        if not isinstance(current_history, list):
                             st.warning(f"History file for {firstname} was corrupted (not a list). Resetting history.")
                             print(f"Warning: History file {history_file_path} was not a list. Resetting.") # Server log
                             current_history = []
                    else:
                        # File exists but is empty
                        current_history = []

            except json.JSONDecodeError:
                 st.warning(f"History file for {firstname} contained invalid JSON. Starting fresh.")
                 print(f"Warning: History file {history_file_path} contained invalid JSON. Starting fresh.") # Server log
                 current_history = []
            except FileNotFoundError:
                 # Should not happen due to check above, but good to be defensive
                 st.error(f"History file {history_file_path} not found unexpectedly.")
                 current_history = []
                 st.stop() # Stop if the file vanished unexpectedly
            except OSError as e:
                 st.error(f"Error reading history file {history_file_path}: {e}")
                 st.stop()


            # Append the new login event
            current_history.append(login_event)

            # Write the updated list back to the file
            try:
                with open(history_file_path, 'w', encoding='utf-8') as f:
                    json.dump(current_history, f, indent=4)
                print(f"Logged login event for {firstname}.")

                # --- !!! SET THE FLAG !!! ---
                # Mark that the login event has been processed for this session
                st.session_state['login_event_logged'] = True
                # -----------------------------

            except OSError as e:
                st.error(f"Error writing history file {history_file_path}: {e}")
                st.stop()


        except OSError as e:
            # Errors related to directory creation or initial file access
            st.error(f"Failed to create or access history directory/file: {e}")
            st.error("Please check folder permissions or contact support.")
            st.stop()
        except Exception as e:
            # Catch other potential errors during file handling
            st.error(f"An unexpected error occurred while processing history: {e}")
            # Optionally set the logged flag to False or delete it if error occurs?
            # Depending on desired behavior. For now, just stop.
            st.stop()
    

# --- START BIRTHDAY CHECK ---
    birthday_str = None # Initialize
    birthday = False

    # Safely retrieve the birthday string from the nested config dictionary
    if config and username:
        try:
            birthday_str = config.get('credentials', {}) \
                                .get('usernames', {}) \
                                .get(username, {}) \
                                .get('birthday') # Returns None if any key is missing or birthday doesn't exist
        except AttributeError:
            # This might happen if config structure is unexpected, though .get should prevent it
            st.warning("Could not read birthday data due to unexpected config structure.")

    # Process the birthday if found
    if birthday_str:
        try:
            # Parse the birthday string - MAKE SURE the format matches config.yaml ('%m/%d/%Y')
            parsed_birthday = datetime.strptime(birthday_str, '%m/%d/%Y').date()
            today = datetime.now().date() # Use datetime.now() for current date/time based on server

            # Compare month and day
            if parsed_birthday.month == today.month and parsed_birthday.day == today.day:
                birthday = True
                st.balloons() # Fun Streamlit effect!
                st.success(f"🎉🎂 Happy Birthday,  {firstname}!!! 🎂🎉")
                st.divider() # Add a divider after the birthday message
            else:
                pass # Or do nothing if it's not their birthday

        except ValueError:
            # Error if the string in config.yaml doesn't match the format '%m/%d/%Y'
            st.warning(f"🎂 Could not understand birthday '{birthday_str}'. Ensure format is MM/DD/YYYY in config.yaml.")
        except Exception as e:
            # Catch any other unexpected errors during date processing
            st.error(f"An error occurred processing birthday: {e}")

# Logout button in sidebar (handled within auth.authenticate's session state setup)
if 'authenticator' in st.session_state:
        st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

if birthday == True:
    if st.sidebar.button("Birthday button!"):
        st.balloons()

def home_parental_view():
    st.title(f"Welcome, {firstname}!")
    st.divider()
    st.subheader("📊 Children's Data")
    if config is None or points_data is None or assignments_data is None or \
        task_templates is None or quest_templates is None or mission_templates is None:
            st.error("Could not load all necessary data...")
            st.error('''This bug was supposed to be fixed - it used to appear all the time, but now it shouldn't any more.
                    I moved the sessions_state.get calls AFTER authentication when they're loaded into the sessions state.
                    Previously, they were before - causing the page to have to be returned to after the session state was loaded.
                    ''')
            st.stop()
    else:
        try:
                # Safely get the list of children assigned to this parent
                parent_config_details = config.get('credentials',{}).get('usernames',{}).get(username,{})
                parent_children_usernames = parent_config_details.get('children', [])
        except Exception as e: # Catch potential errors accessing nested dicts
                st.error(f"Error accessing parent configuration: {e}")
                parent_children_usernames = []

        if not parent_children_usernames:
            st.error(f'''
                        You don't have any children assigned to your account in `config.yaml` under your username's `children:` list.
                        
                        Please screenshot this and send it to Andrew - **this needs to be fixed.**
                        
                        You shouldn't be able to see this; this error is for development only.
                        
                        Role: {st.session_state.get('role')} Username: {st.session_state.get('username')}
                        ''')
            
        else:
            # Display points & activities using columns
            num_kids = len(parent_children_usernames)
            max_cols = 3 # Adjust number of columns for layout
            num_cols = min(num_kids, max_cols)

            if num_cols > 0:
                    cols = st.columns(num_cols)
                    col_index = 0
                    for child_username in parent_children_usernames:
                        child_info = config.get('credentials',{}).get('usernames',{}).get(child_username,{})
                        child_name = child_info.get('name', child_username)
                        child_birthday = child_info.get('birthday', child_username)
                        child_points = points_data.get(child_username, 0)
                        child_points_formatted = f"{child_points:,}"
                        child_firstname = utils.first_name(child_name)

                        # --- Display Column Content ---
                        with cols[col_index % num_cols]:
                            # Display Points Metric
                            with st.container(border=True, height=450):
                                st.subheader(child_name)
                                st.write(f"Birthday: {child_birthday}")
                                st.metric(label=f"👤 {child_firstname}'s points", value=f"{child_points_formatted} pts")
                            
                                # --- Expander for Child's Activities ---
                                with st.expander(f"View {child_firstname}'s Activities", expanded=False):
                                    child_assignments = assignments_data.get(child_username, {})

                                    if not child_assignments:
                                        st.caption("No activities currently assigned.")
                                    else:
                                        # Prepare lists to categorize
                                        missions_list = []
                                        quests_list = []
                                        tasks_list = []

                                        # Categorize assignments
                                        for assign_id, assign_data in child_assignments.items():
                                            item_type = assign_data.get("type")
                                            template_id = assign_data.get("template_id")
                                            status = assign_data.get("status", "Unknown")
                                            info = {"id": template_id, "status": status.replace('_',' ').capitalize()} # Basic info

                                            if item_type == "mission" and template_id:
                                                template = mission_templates.get(template_id, {})
                                                info["name"] = template.get("name", template_id)
                                                info["emoji"] = template.get("emoji", "🗺️")
                                                missions_list.append(info)
                                            elif item_type == "quest" and template_id:
                                                template = quest_templates.get(template_id, {})
                                                info["name"] = template.get("name", template_id)
                                                info["emoji"] = template.get("emoji", "⚔️")
                                                quests_list.append(info)
                                            elif item_type == "task" or item_type == "standalone" and template_id:
                                                template = task_templates.get(template_id, {})
                                                info["name"] = template.get("description", template_id) # Use description for task name
                                                info["emoji"] = template.get("emoji", "📝")
                                                tasks_list.append(info)
                                        # Display categorized lists
                                        if missions_list:
                                            st.write("---")
                                            st.markdown("**Missions:**")
                                            for item in missions_list:
                                                st.echo(f"{st.badge(item['status'])}")
                                                st.write(f"- {item['emoji']} {item['name']}")
                                                    
                                            
                                        if quests_list:
                                            st.write("---")
                                            st.markdown("**Standalone Quests:**")
                                            for item in quests_list:
                                                st.write(f"- {item['emoji']} {item['name']} *(Status: {item['status']})*")
                                            
                                        if tasks_list:
                                            st.write("---")
                                            st.markdown("**Standalone Tasks:**")
                                            for item in tasks_list:
                                                st.write(f"- {item['emoji']} {item['name']} *(Status: {item['status']})*")

                                        if not missions_list and not quests_list and not tasks_list:
                                            st.caption("Could not categorize assigned activities.") # Fallback
                                # --- !!! END EXPANDER !!! ---

                        col_index += 1

def home_kid_view():
    st.title(f"Welcome, {firstname}!")
    st.divider()
    st.subheader("Quick Info")

    completed_tasks = 0
    completed_quests = 0
    completed_missions = 0

    # Check if assignments data is loaded and username exists
    if assignments_data and username:
        user_assignments = assignments_data.get(username, {}) # Get assignments for this user
        for assign_id, assign_data in user_assignments.items():
            status = assign_data.get('status')
            item_type = assign_data.get('type')

            # Count only items marked as completed
            if status == 'completed':
                if item_type == 'mission':
                    completed_missions += 1
                elif item_type == 'quest':
                    # This counts completed *standalone* Quest assignments
                    completed_quests += 1
                elif item_type == 'task':
                    # This counts completed *standalone* Task assignments
                    completed_tasks += 1
                elif item_type == 'standalone':
                    completed_tasks += 1

    # Display the stats using columns and metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Missions Completed 🗺️", value=completed_missions)
    with col2:
        # Clarified label to indicate these are standalone quests/tasks
        st.metric(label="Standalone Quests Completed ⚔️", value=completed_quests)
    with col3:
        st.metric(label="Standalone Tasks Completed 📝", value=completed_tasks)




    if current_points == 0:
        st.write(f"You don't have any points yet! Check your quest board to see if there are any quests that you can begin!")
    else:
        st.write(f"You currently have {current_points} points and have completed {completed_tasks} tasks across {completed_quests} quests in {completed_missions} missions.")
        #st.write(f"**Username:** {st.session_state.get('username')}")
        #st.write(f"**Role:** {st.session_state.get('role', 'Unknown').capitalize()}")
        st.write(f"**Birthday**: {parsed_birthday.strftime('%B %d')}")
        st.sidebar.metric("My Points", current_points, label_visibility="visible", border=True)
        st.sidebar.divider()

if st.session_state.get('role') == 'kid':
    home_kid_view()

if st.session_state.get('role') == 'parent':
    home_parental_view()

if st.session_state.get('role') == 'admin':
    view_columns = st.columns([4,4])
    with view_columns[0]:
        st.header("Parental View")
        with st.container(border=True):
            home_parental_view()
    with view_columns[1]:
        st.header("Kid View")
        with st.container(border=True):
            home_kid_view()
