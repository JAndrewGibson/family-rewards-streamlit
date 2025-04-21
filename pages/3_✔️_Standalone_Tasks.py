import streamlit as st
import utils # Import shared utility functions
import time
import datetime # Needed for acceptance logic maybe?
import auth

# --- Page Configuration ---
st.set_page_config(page_title="Standalone Tasks", page_icon="✔️")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("home.py")
    

# --- Load Data from Session State ---
username = st.session_state.get("username")
mission_templates = st.session_state.get("mission_templates")
quest_templates = st.session_state.get("quest_templates")
task_templates = st.session_state.get("task_templates")
assignments_data = st.session_state.get("assignments")
current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"
POINTS_FILE = 'points.json'

# File path needed for saving
ASSIGNMENTS_FILE = 'assignments.json'

# Check if all necessary data is loaded (Using more verbose checks from previous step)
error_loading = False
if not username: st.error("❌ Username not found."); error_loading = True
if mission_templates is None: st.error("❌ Mission templates missing."); error_loading = True
if quest_templates is None: st.error("❌ Quest templates missing."); error_loading = True
if task_templates is None: st.error("❌ Task templates missing."); error_loading = True
if assignments_data is None: st.error("❌ Assignments data missing."); error_loading = True
if error_loading: st.stop()

if current_points == 0:
    st.sidebar.write('''No points yet! Don't worry, as soon as you earn some points - they'll appear here!
                     ''')
else:
    st.sidebar.metric("My Points", current_points)
    
st.sidebar.divider()

if 'authenticator' in st.session_state:
         st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
        st.sidebar.error("Authenticator not found.")

# --- Page Content ---
if st.session_state.get('role') == 'parent' or st.session_state.get('role') == 'admin':
    st.title("Approve Standalone Tasks")
    config = st.session_state.get('config')
    parent_config_details = config.get('credentials',{}).get('usernames',{}).get(username,{})
    parent_children_usernames = parent_config_details.get('children', [])
    for kid in parent_children_usernames:
        kid_capitalized = kid.title()
        with st.container(border=True):
            st.subheader(kid_capitalized)
            kid_assignments = assignments_data.get(kid, {})
            for assign_id, assign_data in kid_assignments.items():
                if assign_data.get('status') == 'awaiting approval' and assign_data.get('type') == 'standalone':
                    task_id = assign_data.get('task_id') or assign_data.get('template_id') # Handle both keys
                    task_template = task_templates.get(task_id)
                    with st.container(border=True):
                        st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
                        st.caption(task_template.get('description', 'No description.'))
                        st.markdown(f"**Points:** {task_template.get('points', 0)}")
                        if st.button("✅ Complete task", key=f"accept_{assign_id}", use_container_width=True):
                            # Get latest data before modifying
                            current_assigned = utils.load_assignments(ASSIGNMENTS_FILE) # Reload from file just in case
                            if kid in current_assigned and assign_id in current_assigned[kid]:
                                current_assigned[kid][assign_id]['status'] = 'completed'
                                if utils.save_assignments(current_assigned, ASSIGNMENTS_FILE): # Check if save succeeded
                                    st.session_state['assigned_tasks'] = current_assigned # Update state
                                    st.success(f"Task '{task_template.get('name')}' completed!")
                                    current_points = utils.load_points(POINTS_FILE)
                                    print(current_points)
                                    current_points[kid] = current_points.get(kid, 0) + task_template.get('points', 0)
                                    utils.save_points(current_points, POINTS_FILE) # Save points immediately
                                    st.balloons()
                                    time.sleep(2)
                                    current_assigned = utils.load_assignments(ASSIGNMENTS_FILE)
                                    st.rerun()
                else:
                    pass
        print("END KID")

kid_assignments = assignments_data.get(username, {})

pending_assignments = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('status') == 'pending_acceptance' and data.get('type') == 'standalone'
}

active_assignments = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('status') == 'active' and data.get('type') == 'standalone'
}

assignments_awaiting_approval = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('status') == 'awaiting approval' and data.get('type') == 'standalone'
}

completed_assignments = {
    assign_id: data for assign_id, data in kid_assignments.items()
    if data.get('status') == 'completed' and data.get('type') == 'standalone'
}

if st.session_state.get('role') == 'kid' or st.session_state.get('role') == 'admin':
    st.title("✔️ Standalone Tasks")

    # --- TASKS WAITING ON ACCEPTANCE
    if not pending_assignments:
        with st.container(border=True):
            st.subheader("Tasks Awaiting Acceptance")
            st.info("No tasks assigned at this time.")

    else:
        with st.container(border=True):
            st.subheader("Tasks awaiting acceptance")
            
            #Creating the columns and rows
            num_tasks = len(pending_assignments)
            print(num_tasks)
            max_cols = 3
            num_cols = min(num_tasks, max_cols)
            print(num_cols)
            
            if num_cols > 0:
                cols = st.columns(num_cols)
                col_index = 0
            
                for assign_id, assign_data in pending_assignments.items():
                    task_id = assign_data.get('task_id') or assign_data.get('template_id') # Handle both keys
                    task_template = task_templates.get(task_id)
                    
                    with cols[col_index % num_cols]:
                        with st.container(border=True):
                            st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
                            st.caption(task_template.get('description', 'No description.'))
                            st.markdown(f"**Points:** {task_template.get('points', 0)}")

                            # Action Buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Accept task", key=f"accept_{assign_id}", use_container_width=True):
                                    # Get latest data before modifying
                                    current_assigned = utils.load_assignments(ASSIGNMENTS_FILE) # Reload from file just in case
                                    if username in current_assigned and assign_id in current_assigned[username]:
                                        current_assigned[username][assign_id]['status'] = 'active'
                                        if utils.save_assignments(current_assigned, ASSIGNMENTS_FILE): # Check if save succeeded
                                            st.session_state['assigned_tasks'] = current_assigned # Update state
                                            st.success(f"Task '{task_template.get('name')}' accepted!")
                                            time.sleep(2)
                                            current_assigned = utils.load_assignments(ASSIGNMENTS_FILE)
                                            st.rerun()
                                        # Error message is handled within save_assigments
                                    else:
                                        st.error("Could not find assignment to accept. It might have been removed.")

                            with col2:
                                if st.button("❌ Decline Task", key=f"decline_{assign_id}", use_container_width=True):
                                    # Get latest data before modifying
                                    current_assigned = utils.load_assignments(ASSIGNMENTS_FILE)
                                    if username in current_assigned and assign_id in current_assigned[username]:
                                        current_assigned[username][assign_id]['status'] = 'declined'
                                        if utils.save_assignments(current_assigned, ASSIGNMENTS_FILE):
                                            st.session_state['assigned_tasks'] = current_assigned # Update state
                                            st.warning(f"Task '{task_template.get('name')}' declined.")
                                            time.sleep(1)
                                            st.rerun()
                                        # Error message is handled within save_assignments
                                    else:
                                        st.error("Could not find assignment to decline. It might have been removed.")
                        col_index += 1


    # --- ACTIVE TASKS ---     
    if not active_assignments:
        with st.container(border=True):
            st.subheader("Active Tasks")
            st.info("No active tasks")

    else:
        with st.container(border=True):
            st.subheader("Active Tasks")
            
            #Creating the columns and rows
            num_tasks = len(active_assignments)
            print(num_tasks)
            max_cols = 3
            num_cols = min(num_tasks, max_cols)
            print(num_cols)
            
            if num_cols > 0:
                cols = st.columns(num_cols)
                col_index = 0
            
                for assign_id, assign_data in active_assignments.items():
                    task_id = assign_data.get('task_id') or assign_data.get('template_id') # Handle both keys
                    task_template = task_templates.get(task_id)
                    
                    with cols[col_index % num_cols]:
                        with st.container(border=True):
                            st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
                            st.caption(task_template.get('description', 'No description.'))
                            st.markdown(f"**Points:** {task_template.get('points', 0)}")

                            if st.button("✅ Complete task", key=f"accept_{assign_id}", use_container_width=True):
                                # Get latest data before modifying
                                current_assigned = utils.load_assignments(ASSIGNMENTS_FILE) # Reload from file just in case
                                if username in current_assigned and assign_id in current_assigned[username]:
                                    current_assigned[username][assign_id]['status'] = 'awaiting approval'
                                    if utils.save_assignments(current_assigned, ASSIGNMENTS_FILE): # Check if save succeeded
                                        st.session_state['assigned_tasks'] = current_assigned # Update state
                                        st.success(f"Task '{task_template.get('name')}' completed!")
                                        st.balloons()
                                        time.sleep(2)
                                        current_assigned = utils.load_assignments(ASSIGNMENTS_FILE)
                                        st.rerun()
                                    # Error message is handled within save_assigments
                                else:
                                    st.error("Could not find assignment to accept. It might have been removed.")
                        col_index += 1
            
            
    # --- TASKS AWAITING COMPLETION APPROVAL ---
    if not assignments_awaiting_approval:
        with st.container(border=True):
            st.subheader("Task awaiting approval")
            st.info("No tasks awaiting approval.")

    else:
        with st.container(border=True):
            st.subheader("Tasks awaiting approval")
            #Creating the columns and rows
            num_tasks = len(assignments_awaiting_approval)
            print(num_tasks)
            max_cols = 3
            num_cols = min(num_tasks, max_cols)
            print(num_cols)
            
            if num_cols > 0:
                cols = st.columns(num_cols)
                col_index = 0
            
                for assign_id, assign_data in assignments_awaiting_approval.items():
                    task_id = assign_data.get('task_id') or assign_data.get('template_id') # Handle both keys
                    task_template = task_templates.get(task_id)
                    
                    with cols[col_index % num_cols]:
                        with st.container(border=True):
                            st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
                            st.caption(task_template.get('description', 'No description.'))
                            st.markdown(f"**Points:** {task_template.get('points', 0)}")
                        col_index += 1

    # --- COMPLETED TASKS ---
    if not completed_assignments:
        with st.container(border=True):
            st.subheader("Completed Tasks")
            st.info("Looks like you haven't completed any tasks yet.")
        
    else:
        with st.container(border=True):
            st.subheader("Here are all of your completed assignments")
            num_tasks = len(completed_assignments)
            print(num_tasks)
            max_cols = 3
            num_cols = min(num_tasks, max_cols)
            print(num_cols)
            
            if num_cols > 0:
                cols = st.columns(num_cols)
                col_index = 0
            
                for assign_id, assign_data in completed_assignments.items():
                    task_id = assign_data.get('task_id') or assign_data.get('template_id') # Handle both keys
                    task_template = task_templates.get(task_id)
                    
                    with cols[col_index % num_cols]:
                        with st.container(border=True):
                            st.subheader(f"{task_template.get('emoji','❓')} {task_template.get('name','Unnamed Task')}")
                            st.caption(task_template.get('description', 'No description.'))
                            st.markdown(f"**Points:** {task_template.get('points', 0)}")
                        col_index += 1