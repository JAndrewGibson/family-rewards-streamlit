import streamlit as st
import utils # Import shared utility functions
from datetime import datetime
import time # For assignment ID generation
from pathlib import Path
import json
import pandas as pd
import pytz

# --- Page Configuration ---
st.set_page_config(
       page_title="Manage",
       page_icon="⚙️",
       layout="wide",  # Set the layout (wide or centered)
       #initial_sidebar_state="expanded",  # Set the initial sidebar state
       menu_items={
           "Get help": "https://www.example.com",  # Add a custom menu item
           "About" : "Test text"
       }
   )

hide_menu_style = """
    <style>
    .st-emotion-cache-15yi2hn.eecegii10 [data-testid="stMarkdownContainer"] p:last-child {
  display: none !important;
}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# --- Authentication & Authorization Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("home.py")


# --- Load Data from Session State ---
username = st.session_state.get("username")
config = st.session_state.get("config")
mission_templates = st.session_state.get("mission_templates")
quest_templates = st.session_state.get("quest_templates")
task_templates = st.session_state.get("task_templates")
assignments_data = st.session_state.get("assignments")
current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"
name = st.session_state['name']


# File paths
TASKS_TEMPLATE_FILE = 'tasks.json'
QUESTS_TEMPLATE_FILE = 'quests.json'
MISSIONS_TEMPLATE_FILE = 'missions.json'
ASSIGNED_QUESTS_FILE = 'assignments.json'
HISTORY_FOLDER = Path("user_history")
HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = 'config.yaml'
ALL_TIMEZONES = sorted(pytz.all_timezones)


# --- Load Data (Load fresh for management/assignment actions) ---
user_config_details = config.get('credentials',{}).get('usernames',{}).get(username,{})
user_timezone = user_config_details.get('timezone', [])
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
safe_filename = f"{username}_history.json"
history_file_path = HISTORY_FOLDER / safe_filename

with st.sidebar:
    current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
    current_points = f"{current_points_unformatted:,}"
    st.metric("My Points", current_points, label_visibility="visible", border=True)
    st.divider()

if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

# Handle loading errors
if task_templates is None or quest_templates is None or mission_templates is None or assignments_data is None:
    st.error("Failed to load one or more data files. Cannot proceed.")
    st.stop()


def manage_kid_view(user_timezone):
    tab_list = [
    "🗝️ History",
    "🧑🏽‍💻Code",
    "⚙️User Settings",
    ]
    tab1, tab2, tab3 = st.tabs(tab_list)
    
    with tab1:
         if st.session_state.get('role'):
            st.header("EVENT HISTORY") # Moved header inside the check for consistency

            # Ensure we have the user's username and timezone
            if not username:
                st.warning("Cannot display history: User information not found.")
            # Ensure the timezone variable exists and is not empty
            elif not user_timezone:
                st.warning(f"Cannot display history in local time for user '{username}': User timezone not set.")
                user_timezone = "UTC"
                st.info("Displaying timestamps in UTC.")
            else:
                try:
                    # Construct the path to the user's history file
                    safe_filename = f"{username}_history.json"
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

                                # --- Data Cleaning and Formatting ---

                                # Check if 'timestamp' column exists before processing
                                if 'timestamp' in df_history.columns:

                                    # 1. Convert timestamp string to datetime objects (make them UTC aware)
                                    #    errors='coerce' turns unparseable strings/None into NaT (Not a Time)
                                    #    utc=True ensures they are treated as UTC if no offset was present (though yours have it)
                                    df_history['timestamp'] = pd.to_datetime(df_history['timestamp'], errors='coerce', utc=True)

                                    # --- *** ADD TIMEZONE CONVERSION HERE *** ---
                                    try:
                                        # 2. Convert the UTC datetime objects to the user's local timezone
                                        #    This operation only works on valid datetime objects (not NaT)
                                        #    Use .loc to avoid SettingWithCopyWarning if df_history is a slice
                                        valid_timestamps = df_history['timestamp'].notna()
                                        df_history.loc[valid_timestamps, 'timestamp'] = df_history.loc[valid_timestamps, 'timestamp'].dt.tz_convert(user_timezone)
                                        # Now the 'timestamp' column holds timezone-aware datetimes localized to user_timezone

                                    except Exception as tz_error:
                                        st.error(f"Could not convert timestamps to timezone '{user_timezone}'. Displaying in UTC. Error: {tz_error}")
                                        print(f"Timezone conversion error for user {username}, tz {user_timezone}: {tz_error}")
                                        # If conversion fails, timestamps remain UTC (from pd.to_datetime)


                                    # 3. Sort by timestamp (most recent first). NaT values will be sorted last.
                                    df_history = df_history.sort_values(by='timestamp', ascending=False, na_position='last')

                                    # 4. Select and reorder columns for display
                                    display_columns = ['timestamp', 'event_type', 'message', 'affected_item', 'user']
                                    existing_columns = [col for col in display_columns if col in df_history.columns]
                                    df_display = df_history[existing_columns].copy() # Create a copy for display modification
                                    
                                    if 'timestamp' in df_display.columns:
                                        df_display['timestamp'] = df_display['timestamp'].dt.strftime('%d/%m/%y %H:%M:%S')
                                        df_display['timestamp'] = df_display['timestamp'].fillna("N/A")


                                    # --- Display the DataFrame ---
                                    st.dataframe(
                                        df_display,
                                        use_container_width=True, # Make table use full tab width
                                        hide_index=True # Hide the default numerical index
                                    )
                                else:
                                    # Handle case where 'timestamp' column is missing entirely
                                    st.warning("History data is missing the 'timestamp' column.")
                                    # Display remaining data if useful
                                    df_display = df_history[[col for col in df_history.columns if col != 'timestamp']]
                                    if not df_display.empty:
                                        st.dataframe(df_display, use_container_width=True, hide_index=True)


                    else:
                        # File doesn't exist for this user
                        st.info(f"No history found for user '{username}'.") # Use username variable

                except json.JSONDecodeError:
                    st.error("Failed to read history file: Invalid format.")
                    print(f"Error: JSONDecodeError reading {history_file_path}") # Server log
                except FileNotFoundError:
                    # This case is handled by the is_file() check above, but good practice
                    st.info(f"No history found for user '{username}'.") # Use username variable
                except OSError as e:
                    st.error(f"An error occurred while accessing history file: {e}")
                    print(f"Error: OSError accessing {history_file_path}: {e}") # Server log
                except Exception as e:
                    st.error(f"An unexpected error occurred while displaying history: {e}")
                    # Use username in server log for clarity
                    print(f"Error: Unexpected error displaying history for {username}: {e}") # Server log
    
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
         
    with tab3:
        if st.session_state.get('role') == 'kid':
            st.header(f"⚙️{firstname}'s User Settings")

            st.subheader(f"Settings for {firstname}")

            # --- Timezone Setting ---
            st.divider()
            st.markdown("#### Timezone")

            # Make sure config loaded successfully and has the expected structure
            if config and 'credentials' in config and 'usernames' in config['credentials']:
                user_credentials = config['credentials']['usernames']

                if username in user_credentials:
                    user_data = user_credentials[username]
                    # Get current timezone, default to UTC if not set (optional)
                    current_timezone = user_data.get("timezone", "UTC")

                    # Find the index of the current timezone in the list for dropdown default
                    try:
                        # Ensure the current timezone is actually in our list
                        if current_timezone not in ALL_TIMEZONES:
                            # If not, add it temporarily so it can be selected, warn user
                            st.warning(f"Saved timezone '{current_timezone}' is not a standard IANA zone. Adding it to the list.")
                            ALL_TIMEZONES.insert(0, current_timezone) # Add to beginning
                            current_tz_index = 0
                        else:
                            current_tz_index = ALL_TIMEZONES.index(current_timezone)

                    except ValueError:
                        # This shouldn't happen if the check above works, but as a fallback
                        st.error(f"Could not find index for current timezone '{current_timezone}'. Defaulting selection.")
                        current_tz_index = ALL_TIMEZONES.index("UTC") # Default to UTC index

            # Create the dropdown (selectbox)
            new_timezone = st.selectbox(
                "Select your preferred timezone:",
                options=ALL_TIMEZONES,
                index=current_tz_index,
                key="timezone_select",
                help="I manually set everyone's timezone up, so it should be on the correct one automatically. -Andrew"
            )

            # Create the save button
            if st.button("Save Timezone", key="save_tz_button"):
                        if new_timezone != current_timezone:
                            # --- Update Logic ---
                            # Load the config again right before saving to minimize race conditions
                            latest_config = utils.load_config(CONFIG_PATH)
                            if latest_config and 'credentials' in latest_config and 'usernames' in latest_config['credentials'] and username in latest_config['credentials']['usernames']:
                                # Update the timezone for the specific user
                                latest_config['credentials']['usernames'][username]['timezone'] = new_timezone

                                # Save the modified data back to the file
                                if utils.save_config(CONFIG_PATH, latest_config):
                                    st.success(f"Timezone updated to {new_timezone}!")
                                    # Optional: Update session state if you use it for immediate effect elsewhere
                                    if 'user_timezone' in st.session_state:
                                        st.session_state['user_timezone'] = new_timezone
                                    # Rerun the script to reflect the change immediately in the selectbox default
                                    st.rerun()
                                else:
                                    # save_config would have shown an error
                                    pass
                            else:
                                st.error("Failed to reload configuration before saving. Please try again.")

                        else:
                            st.info("No changes made to timezone.")
        
            if st.button(label="Balloons", key="kid_balloons"):
                    st.balloons()
                    time.sleep(.5)
                    st.balloons()
                    time.sleep(.5)
                    st.balloons()
                    time.sleep(.5)
                    st.balloons()
            if st.button(label="Blizzard", key="kid_blizzard"):
                st.snow()
                time.sleep(.5)
                st.snow()
                time.sleep(.5)
                st.snow()
                time.sleep(.5)
        
        else:
            st.header("🤠 Hold it right there cowboy!")
            st.write("Looks like you're logged in as an Admin. To avoid duplicate rendering - this portion is not shown. Please adjust user settings from parental part of the app.")
            with st.container(border=True):
                st.subheader(f"Some very secret admin-only buttons...")
                if st.button(label="Balloons"):
                    st.balloons()
                    time.sleep(.5)
                    st.balloons()
                    time.sleep(.5)
                    st.balloons()
                    time.sleep(.5)
                    st.balloons()
                if st.button(label="Blizzard"):
                    st.snow()
                    time.sleep(.5)
                    st.snow()
                    time.sleep(.5)
                    st.snow()
                    time.sleep(.5)

def manage_parental_view(user_timezone):
    # --- Define Tabs ---
    tab_list = [
        "📝 Tasks",
        "⚔️ Quests",
        "🗺️ Missions",
        "💎 Rewards",
        "🎯 Assign",
        "🗝️ History",
        "⚙️ User Settings"
    ]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_list)

    with tab1:
        st.header("📝 Standalone Task Form")
        st.caption("Define individual tasks.")

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
            cols4 = st.columns([4,4])
            new_task_id = cols4[0].text_input("Task ID :",help="Task IDs should be unique - you can name them anything you'd like; I'd recommend naming it (child_task_number)")
            new_task_name = cols4[1].text_input("Task Name:", help="Doesn't need to be unique - but it will make things a lot easier if it is.")
            new_task_desc = st.text_area("Description:", help="Description will be shown to the child on what exactly they need to do to mark the task as complete!")
            cols5 = st.columns([4,4])
            new_task_points = cols5[0].number_input("Points:", min_value=0, step=1, value=10)
            new_task_emoji = cols5[1].text_input("Emoji Icon:", help="On a computer? Use Win + . to pick emojis on Windows!", max_chars=2)

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
                        if utils.log_into_history(event_type="task_created", message=f"{username} created new task '{new_task_name}'.",affected_item=new_task_id, username=username):
                            st.success("Successfully logged task creation event!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Could not log task creation. Please tell Andrew.")
                            time.sleep(10)
                            st.rerun()
                        # --- END HISTORY LOGGING FOR TASK CREATION ---
                    else:
                        # Error message handled by save function, remove potentially corrupt data
                        del task_templates[new_task_id] # Roll back change if save failed
                    
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
        st.subheader("Create New Quest Template") # Changed subheader slightly

        # Initialize session state list for tasks in the current quest being built/edited
        if 'current_quest_tasks' not in st.session_state:
            st.session_state.current_quest_tasks = []


        with st.form("new_quest_form"): # Don't clear on submit automatically
            cols2 = st.columns([4,4])
            new_quest_id = cols2[0].text_input("Quest ID:", help="Must be unique", key="quest_form_id")
            new_quest_name = cols2[1].text_input("Quest Name:", key="quest_form_name")
            new_quest_desc = st.text_area("Description:", key="quest_form_desc",)
            cols3 = st.columns([4,4])
            new_quest_emoji = cols3[1].text_input("Emoji Icon:", max_chars=2, key="quest_form_emoji")
            new_quest_bonus = cols3[0].number_input("Completion Bonus Points:", min_value=0, step=50, value=50, key="quest_form_bonus",)
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
                        if utils.log_into_history(event_type="quest_created", message=f"{username} created new quest '{new_quest_name}'.",affected_item=new_quest_id, username=username):
                           st.success("New quest creation logged into history!")
                           time.sleep(2)
                           st.rerun() # Use if form fields don't clear properly
                        else:
                            st.error("Error logging new quest creation into history! Please tell Andrew!")
                        st.session_state.current_quest_tasks = []
                    else:
                        #SAVE FAILED! ROLLING BACK
                        st.error("Saving failed. Please check permissions or logs.")
                        del quest_templates[new_quest_id] # Remove quest 

        # --- "Add Task Step" Button (Outside the form) ---
        if st.button("➕ Add Task Step to Quest Definition"):
            # Add a new blank task structure to the list in session state
            st.session_state.current_quest_tasks.append({"id": "", "description": "", "points": 0, "emoji": ""})
            st.rerun()

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
            cols6 = st.columns([4,4])
            new_mission_id = cols6[0].text_input("Mission ID (must be unique):",key="new_mission_id")
            new_mission_name = cols6[1].text_input("Mission Name:", key="new_mission_name")
            new_mission_desc = st.text_area("Description:", key="new_mission_desc")
            new_mission_emoji = st.text_input("Emoji Icon:", max_chars=4, key="new_mission_emoji")
            st.divider()

            # --- Select Contained Items ---
            st.markdown("**Select Components for this Mission:**")
            quest_options_map = {qid: utils.get_item_display_name(qid, quest_templates, task_templates) for qid in quest_templates}
            cols7 = st.columns([4,4])
            selected_quest_ids = cols7[0].multiselect(
                "Include Quests:",
                options=list(quest_options_map.keys()),
                format_func=lambda qid: quest_options_map[qid],
                key="mission_quests_select"
            )

            task_options_map = {tid: utils.get_item_display_name(tid, quest_templates, task_templates) for tid in task_templates}
            selected_task_ids = cols7[1].multiselect(
                "Include Standalone Tasks:",
                options=list(task_options_map.keys()),
                format_func=lambda tid: task_options_map[tid],
                key="mission_tasks_select"
            )

            # Combine all selected items for prerequisite definition
            all_selected_items = selected_quest_ids + selected_task_ids
            all_selected_items_map = { # Map IDs to display names for dropdown options
                item_id: utils.get_item_display_name(item_id, quest_templates, task_templates)
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
                        if utils.log_into_history(event_type="mision_created", message=f"{username} created new mission '{new_mission_name}'.", affected_item=new_mission_id, username=username):
                            st.success("New mission creation event added to history.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Could not save mission creation event in history! Please tell Andrew!")

                    else:
                        # Save failed, roll back if needed
                        if mission_id in mission_templates: del mission_templates[mission_id]
                        # Error message is shown by save function
     
    with tab4:
        st.header("💎 Create rewards!")
        with st.form("new_reward_form", clear_on_submit=True):
            new_reward_id = st.text_input("Reward ID")
            new_reward_name = st.text_input("Reward Name")
            new_reward_description = st.text_area("Description:")
            new_reward_points = st.number_input("Points:", min_value=0, step=1, value=0)
            new_reward_image = st.text_input("Place the URL to the image here!", placeholder="https://picsum.photos/200/300")
            st.caption('''Why can't you upload a photo? Because image hosting is expensive and there are a trillion images on the internet which you can use that are already hosted. 😅 AI generate one and upload it to an image hosting site if you really want a custom image.''')
            submitted_reward = st.form_submit_button("Save Reward")
    
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
                                try:
                                    utils.save_assignments(current_assignments, ASSIGNED_QUESTS_FILE)
                                    print("DEBUG SAVED ASSIGNMENT")
                                    st.session_state['assigned_quests'] = current_assignments # Update session state
                                    print("SAVE NEW SESSION STATE")
                                    utils.log_into_history(event_type=f"{type_prefix}_assigned", message=(f"{username} assigned new {type_prefix} to {selected_kid_username}"), affected_item=selected_template_id, username=username)
                                    print("DEBUG: logged event")
                                    st.success(f"{assign_type} '{template_options.get(selected_template_id, selected_template_id)}' assigned to {selected_kid_display_name} for acceptance!")
                                    print("DEBUG: NOW WAIT...")
                                    time.sleep(2)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to create history file: {e}")
                                    print("THERE'S AN EXCEPTION")
                                    st.error("Failed to save assignment - please screenshot this and send it to Andrew.")
                                    st.stop()

                        else:
                            st.warning("Please ensure a child and an activity template are selected.")
    
    with tab6:
        if st.session_state.get('role'):
            st.header("History Logs") # Moved header inside the check for consistency

            # Ensure we have the user's username and timezone
            if not username:
                st.warning("Cannot display history: User information not found.")
            # Ensure the timezone variable exists and is not empty
            elif not user_timezone:
                st.warning(f"Cannot display history in local time for user '{username}': User timezone not set.")
                # Decide how to proceed: Display in UTC? Show an error?
                # Here we'll default to UTC if not set, or you could stop.
                user_timezone = "UTC" # Fallback or handle error differently
                st.info("Displaying timestamps in UTC.")
            else:
                try:
                    # Construct the path to the user's history file
                    safe_filename = f"{username}_history.json"
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

                                # --- Data Cleaning and Formatting ---

                                # Check if 'timestamp' column exists before processing
                                if 'timestamp' in df_history.columns:

                                    # 1. Convert timestamp string to datetime objects (make them UTC aware)
                                    #    errors='coerce' turns unparseable strings/None into NaT (Not a Time)
                                    #    utc=True ensures they are treated as UTC if no offset was present (though yours have it)
                                    df_history['timestamp'] = pd.to_datetime(df_history['timestamp'], errors='coerce', utc=True)

                                    # --- *** ADD TIMEZONE CONVERSION HERE *** ---
                                    try:
                                        # 2. Convert the UTC datetime objects to the user's local timezone
                                        #    This operation only works on valid datetime objects (not NaT)
                                        #    Use .loc to avoid SettingWithCopyWarning if df_history is a slice
                                        valid_timestamps = df_history['timestamp'].notna()
                                        df_history.loc[valid_timestamps, 'timestamp'] = df_history.loc[valid_timestamps, 'timestamp'].dt.tz_convert(user_timezone)
                                        # Now the 'timestamp' column holds timezone-aware datetimes localized to user_timezone

                                    except Exception as tz_error:
                                        st.error(f"Could not convert timestamps to timezone '{user_timezone}'. Displaying in UTC. Error: {tz_error}")
                                        print(f"Timezone conversion error for user {username}, tz {user_timezone}: {tz_error}")
                                        # If conversion fails, timestamps remain UTC (from pd.to_datetime)


                                    # 3. Sort by timestamp (most recent first). NaT values will be sorted last.
                                    df_history = df_history.sort_values(by='timestamp', ascending=False, na_position='last')

                                    # 4. Select and reorder columns for display
                                    display_columns = ['timestamp', 'event_type', 'message', 'affected_item', 'user']
                                    existing_columns = [col for col in display_columns if col in df_history.columns]
                                    df_display = df_history[existing_columns].copy() # Create a copy for display modification
                                    
                                    if 'timestamp' in df_display.columns:
                                        df_display['timestamp'] = df_display['timestamp'].dt.strftime('%d/%m/%y %H:%M:%S')
                                        df_display['timestamp'] = df_display['timestamp'].fillna("N/A")


                                    # --- Display the DataFrame ---
                                    st.dataframe(
                                        df_display,
                                        use_container_width=True, # Make table use full tab width
                                        hide_index=True # Hide the default numerical index
                                    )
                                else:
                                    # Handle case where 'timestamp' column is missing entirely
                                    st.warning("History data is missing the 'timestamp' column.")
                                    # Display remaining data if useful
                                    df_display = df_history[[col for col in df_history.columns if col != 'timestamp']]
                                    if not df_display.empty:
                                        st.dataframe(df_display, use_container_width=True, hide_index=True)


                    else:
                        # File doesn't exist for this user
                        st.info(f"No history found for user '{username}'.") # Use username variable

                except json.JSONDecodeError:
                    st.error("Failed to read history file: Invalid format.")
                    print(f"Error: JSONDecodeError reading {history_file_path}") # Server log
                except FileNotFoundError:
                    # This case is handled by the is_file() check above, but good practice
                    st.info(f"No history found for user '{username}'.") # Use username variable
                except OSError as e:
                    st.error(f"An error occurred while accessing history file: {e}")
                    print(f"Error: OSError accessing {history_file_path}: {e}") # Server log
                except Exception as e:
                    st.error(f"An unexpected error occurred while displaying history: {e}")
                    # Use username in server log for clarity
                    print(f"Error: Unexpected error displaying history for {username}: {e}") # Server log



    with tab7:
        st.header(f"⚙️{firstname}'s User Settings")

        st.subheader(f"Settings for {firstname}")
        st.text_input(label="Man, I wish the settings page had the ability to...")
        # --- Timezone Setting ---
        st.divider()
        st.markdown("#### Timezone")

        # Make sure config loaded successfully and has the expected structure
        if config and 'credentials' in config and 'usernames' in config['credentials']:
            user_credentials = config['credentials']['usernames']

            if username in user_credentials:
                user_data = user_credentials[username]
                # Get current timezone, default to UTC if not set (optional)
                current_timezone = user_data.get("timezone", "UTC")

                # Find the index of the current timezone in the list for dropdown default
                try:
                    # Ensure the current timezone is actually in our list
                    if current_timezone not in ALL_TIMEZONES:
                        # If not, add it temporarily so it can be selected, warn user
                        st.warning(f"Saved timezone '{current_timezone}' is not a standard IANA zone. Adding it to the list.")
                        ALL_TIMEZONES.insert(0, current_timezone) # Add to beginning
                        current_tz_index = 0
                    else:
                        current_tz_index = ALL_TIMEZONES.index(current_timezone)

                except ValueError:
                    # This shouldn't happen if the check above works, but as a fallback
                    st.error(f"Could not find index for current timezone '{current_timezone}'. Defaulting selection.")
                    current_tz_index = ALL_TIMEZONES.index("UTC") # Default to UTC index

                # Create the dropdown (selectbox)
                new_timezone = st.selectbox(
                    "Select your preferred timezone:",
                    options=ALL_TIMEZONES,
                    index=current_tz_index,
                    key="timezone_select",
                    help="I manually set everyone's timezone up, so it should be on the correct one automatically. -Andrew"
                )

                # Create the save button
                if st.button("Save Timezone", key="save_tz_button"):
                    if new_timezone != current_timezone:
                        # --- Update Logic ---
                        # Load the config again right before saving to minimize race conditions
                        latest_config = utils.load_config(CONFIG_PATH)
                        if latest_config and 'credentials' in latest_config and 'usernames' in latest_config['credentials'] and username in latest_config['credentials']['usernames']:
                            # Update the timezone for the specific user
                            latest_config['credentials']['usernames'][username]['timezone'] = new_timezone

                            # Save the modified data back to the file
                            if utils.save_config(CONFIG_PATH, latest_config):
                                st.success(f"Timezone updated to {new_timezone}!")
                                # Optional: Update session state if you use it for immediate effect elsewhere
                                if 'user_timezone' in st.session_state:
                                    st.session_state['user_timezone'] = new_timezone
                                # Rerun the script to reflect the change immediately in the selectbox default
                                st.rerun()
                            else:
                                # save_config would have shown an error
                                pass
                        else:
                            st.error("Failed to reload configuration before saving. Please try again.")

                    else:
                        st.info("No changes made to timezone.")

# PARENTAL VIEW
if st.session_state.get('role') == 'parent':
    manage_parental_view(user_timezone)

# KID VIEW
if st.session_state.get('role') == 'kid':
    manage_kid_view(user_timezone)
                
# ADMIN VIEW
if st.session_state.get('role') == 'admin':
    full_page_columns = st.columns([4,4])
    with full_page_columns[0]:
        st.title("Parental View")
        st.divider()
        manage_parental_view(user_timezone)
    with full_page_columns[1]:
        st.title("Child's View")
        st.divider()
        manage_kid_view(user_timezone)
    with st.container(border=True):
        st.header("Showing Admin-Only Options:")
        with st.expander("DEBUG: Session State"):
            st.write(st.session_state)