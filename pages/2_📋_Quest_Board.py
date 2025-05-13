import streamlit as st
import time
import utils
from pathlib import Path
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Quest Board", page_icon="📋", layout="wide")

# --- Authentication Check ---
if st.session_state.get('authentication_status') is not True:
    st.switch_page("Home.py")


# --- Load Data from Session State ---
username = st.session_state.get("username")
mission_templates = st.session_state.get("mission_templates")
quest_templates = st.session_state.get("quest_templates")
task_templates = st.session_state.get("task_templates")
assignments_data = st.session_state.get("assignments")
current_points_unformatted = st.session_state.get('points', {}).get(username, 0)
current_points = f"{current_points_unformatted:,}"
user_points_data = st.session_state.get("points", {})

# File paths
POINTS_FILE = 'points.json'
ASSIGNMENTS_FILE = 'assignments.json'
USER_HISTORY_DIR = "user_history"

# Check if all necessary data is loaded
if not all([username, mission_templates is not None, quest_templates is not None, task_templates is not None, assignments_data is not None, user_points_data is not None]):
    missing = [item_name for item_name, item_val in [("Username", username), ("Mission Templates", mission_templates),
                                                     ("Quest Templates", quest_templates), ("Task Templates", task_templates),
                                                     ("Assignments", assignments_data), ("Points Data", user_points_data)] if item_val is None]
    st.error(f"❌ Critical data missing from session state: {', '.join(missing)}. Please log out and back in.")
    st.stop()

current_user_points = user_points_data.get(username, 0)
user_assignments = assignments_data.get(username, {})


# --- Sidebar ---
st.sidebar.metric("My Points", f"{current_user_points:,}", label_visibility="visible")
st.sidebar.divider()
if st.sidebar.button("🔄 Refresh Data"):
    st.session_state['assignments'] = utils.load_assignments(ASSIGNMENTS_FILE)
    st.session_state['points'] = utils.load_points(POINTS_FILE)
    # Potentially reload other templates if they can change, though less common for user-facing pages
    st.rerun()

if 'authenticator' in st.session_state and hasattr(st.session_state['authenticator'], 'logout'):
     st.session_state['authenticator'].logout('Logout', 'sidebar')
else:
     st.sidebar.warning("Logout functionality not available - this is literally impossible, because there's another auth check above this. If you're seeing this, something is SERIOUSLY BROKE, tell Andrew.")


# --- Helper function to get sub-task details and progress ---
def get_quest_sub_task_details(quest_assign_id, quest_template_id, user_task_assignments):
    quest_template = quest_templates.get(quest_template_id, {})
    sub_task_template_ids = quest_template.get('tasks', [])
    if not sub_task_template_ids:
        return [], 0, 0 # No sub-tasks defined in template

    completed_sub_tasks_count = 0
    linked_sub_task_details = []
    actual_sub_task_assignments_count = 0

    for task_assign_id, task_data in user_task_assignments.items():
        if task_data.get('type') == 'task' and task_data.get('quest_id') == quest_assign_id:
            actual_sub_task_assignments_count +=1
            task_template = task_templates.get(task_data['template_id'], {})
            status = task_data.get('status', 'unknown')
            detail = {
                "name": task_template.get('name', 'Unknown Task'),
                "status": status,
                "points": task_template.get('points', 0)
            }
            linked_sub_task_details.append(detail)
            if status == 'completed':
                completed_sub_tasks_count += 1
    
    # Check if all defined sub_task_template_ids have corresponding assignments
    # This indicates whether the assignment process correctly created all sub-tasks.
    # For simplicity here, we'll use the count of defined sub-tasks in the template as the total.
    total_sub_tasks_in_template = len(sub_task_template_ids)

    return linked_sub_task_details, completed_sub_tasks_count, total_sub_tasks_in_template

# --- Page Content ---
st.title("📋 Quest Board")
st.markdown("Manage your assigned quests. Accept new challenges, track your progress, and complete them to earn rewards!")
st.divider()

# --- Section 1: Quests Pending My Acceptance ---
st.header("⏳ Quests Pending My Acceptance")
pending_quests = {
    assign_id: data for assign_id, data in user_assignments.items()
    if data.get('type') == 'quest' and data.get('status') == 'pending_acceptance'
}

if not pending_quests:
    st.info("No quests are currently pending your acceptance. Great job staying on top of things!")
else:
    for assign_id, assign_data in pending_quests.items():
        quest_template_id = assign_data.get('template_id')
        quest_template = quest_templates.get(quest_template_id, {})
        if not quest_template:
            st.warning(f"Could not find quest template for assignment {assign_id}. Skipping.")
            continue

        with st.container(border=True):
            st.subheader(f"{quest_template.get('icon', '🎯')} {quest_template.get('name', 'Unnamed Quest')}")
            cols = st.columns([3,1])
            with cols[0]:
                st.markdown(f"**Description:** {quest_template.get('description', 'No description available.')}")
                st.markdown(f"**Reward:** {quest_template.get('points', 0):,} Points")
                mission_id = assign_data.get('mission_id')
                if mission_id:
                    mission_template_id = assignments_data.get(username, {}).get(mission_id, {}).get('template_id')
                    mission_name = mission_templates.get(mission_template_id, {}).get('name', 'Unknown Mission')
                    st.caption(f"Part of Mission: {mission_name}")

                sub_task_ids_in_template = quest_template.get('tasks', [])
                if sub_task_ids_in_template:
                    with st.expander("Tasks in this Quest"):
                        for task_tid in sub_task_ids_in_template:
                            st.error(f"DEBUG: {task_templates}")
                            task_t = task_templates.get(task_tid, {})
                            st.markdown(f"- {task_t.get('name', 'Unknown Task')} ({task_t.get('points',0)} pts)")
            with cols[1]:
                if st.button("✅ Accept Quest", key=f"accept_quest_{assign_id}", use_container_width=True, type="primary"):
                    all_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                    if username in all_assignments and assign_id in all_assignments[username]:
                        all_assignments[username][assign_id]['status'] = 'active'
                        all_assignments[username][assign_id]['accepted_on'] = datetime.now().isoformat()
                        if utils.save_assignments(all_assignments, ASSIGNMENTS_FILE):
                            st.session_state['assignments'] = all_assignments
                            utils.record_history(username, "Quest Accepted", f"Accepted quest: {quest_template.get('name')}", quest_template.get('points', 0), USER_HISTORY_DIR)
                            st.success(f"Quest '{quest_template.get('name')}' accepted!")
                            time.sleep(0.5) # Brief pause to see message
                            st.rerun()
                        else:
                            st.error("Failed to save quest acceptance.")
                    else:
                        st.error("Quest not found for acceptance. It might have been modified.")

                if st.button("❌ Decline Quest", key=f"decline_quest_{assign_id}", use_container_width=True):
                    all_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                    if username in all_assignments and assign_id in all_assignments[username]:
                        all_assignments[username][assign_id]['status'] = 'declined'
                        all_assignments[username][assign_id]['declined_on'] = datetime.now().isoformat()
                        if utils.save_assignments(all_assignments, ASSIGNMENTS_FILE):
                            st.session_state['assignments'] = all_assignments
                            utils.record_history(username, "Quest Declined", f"Declined quest: {quest_template.get('name')}", 0, USER_HISTORY_DIR)
                            st.warning(f"Quest '{quest_template.get('name')}' declined.")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to save quest decline.")
                    else:
                        st.error("Quest not found for decline.")
st.divider()

# --- Section 2: My Active Quests ---
st.header("💪 My Active Quests")
active_quests = {
    assign_id: data for assign_id, data in user_assignments.items()
    if data.get('type') == 'quest' and data.get('status') == 'active'
}

if not active_quests:
    st.info("You have no active quests. Accept one from the 'Pending Acceptance' section or check the 'Missions' page!")
else:
    for assign_id, assign_data in active_quests.items():
        quest_template_id = assign_data.get('template_id')
        quest_template = quest_templates.get(quest_template_id, {})
        if not quest_template:
            st.warning(f"Could not find quest template for active quest {assign_id}. Skipping.")
            continue

        sub_task_details, completed_count, total_count = get_quest_sub_task_details(assign_id, quest_template_id, user_assignments)

        with st.container(border=True):
            st.subheader(f"{quest_template.get('icon', '🚀')} {quest_template.get('name', 'Unnamed Quest')}")
            st.markdown(f"**Description:** {quest_template.get('description', 'No description available.')}")
            st.markdown(f"**Reward:** {quest_template.get('points', 0):,} Points")
            mission_id = assign_data.get('mission_id')
            if mission_id:
                mission_template_id = assignments_data.get(username, {}).get(mission_id, {}).get('template_id')
                mission_name = mission_templates.get(mission_template_id, {}).get('name', 'Unknown Mission')
                st.caption(f"Part of Mission: {mission_name}")


            if total_count > 0:
                st.progress(completed_count / total_count if total_count > 0 else 0, text=f"{completed_count}/{total_count} tasks completed")
                with st.expander("View Sub-Tasks and Status"):
                    if not sub_task_details:
                         st.caption("No sub-tasks assigned or found for this quest. This might be an error in assignment.")
                    for task_detail in sub_task_details:
                        task_status_icon = "✅" if task_detail['status'] == 'completed' else ("⏳" if task_detail['status'] == 'pending_approval' else ("➡️" if task_detail['status'] == 'active' else "❔"))
                        st.markdown(f"{task_status_icon} {task_detail['name']} ({task_detail['status']})")
                    if not sub_task_details and quest_template.get('tasks'):
                        st.caption("Sub-tasks are defined for this quest but might not have been assigned to you yet. Check with Andrew.")


            action_cols = st.columns(2)
            with action_cols[0]:
                # Enable completion request if all sub-tasks are done, or if there are no sub-tasks (quest is atomic)
                can_complete_quest = (total_count > 0 and completed_count == total_count) or (total_count == 0)
                if st.button("🏁 Request Quest Completion", key=f"complete_quest_{assign_id}", disabled=not can_complete_quest, use_container_width=True, type="primary"):
                    all_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                    current_points_data = utils.load_points(POINTS_FILE) # Load fresh points data

                    if username in all_assignments and assign_id in all_assignments[username]:
                        # For now, let's assume quests go to 'pending_approval' like tasks.
                        # If some quests can be auto-completed, this logic would need a flag on the quest_template.
                        new_status = 'pending_approval' # or 'completed' if no approval step for quests
                        completion_message = f"Quest '{quest_template.get('name')}' submitted for approval!"

                        # If quests are directly completed and points awarded here (example):
                        # new_status = 'completed'
                        # points_to_award = quest_template.get('points', 0)
                        # current_points_data[username] = current_points_data.get(username, 0) + points_to_award
                        # completion_message = f"Quest '{quest_template.get('name')}' completed! +{points_to_award:,} points!"
                        # utils.save_points(current_points_data, POINTS_FILE)
                        # st.session_state['points'] = current_points_data


                        all_assignments[username][assign_id]['status'] = new_status
                        all_assignments[username][assign_id]['completed_on'] = datetime.now().isoformat() # Or 'submitted_for_approval_on'

                        if utils.save_assignments(all_assignments, ASSIGNMENTS_FILE):
                            st.session_state['assignments'] = all_assignments
                            utils.record_history(username, "Quest Completion Requested", f"Requested completion for: {quest_template.get('name')}", quest_template.get('points', 0), USER_HISTORY_DIR)
                            st.success(completion_message)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to save quest completion request.")
                    else:
                        st.error("Quest not found for completion.")
                if not can_complete_quest and total_count > 0:
                    st.caption("Complete all sub-tasks to enable quest completion.")
                elif not can_complete_quest and total_count == 0:
                    st.caption("This quest has no defined sub-tasks. You can request completion directly.")


            with action_cols[1]:
                if st.button("💔 Abandon Quest", key=f"abandon_quest_{assign_id}", use_container_width=True):
                    # Add confirmation later if desired st.confirm()
                    all_assignments = utils.load_assignments(ASSIGNMENTS_FILE)
                    if username in all_assignments and assign_id in all_assignments[username]:
                        all_assignments[username][assign_id]['status'] = 'abandoned'
                        all_assignments[username][assign_id]['abandoned_on'] = datetime.now().isoformat()
                        if utils.save_assignments(all_assignments, ASSIGNMENTS_FILE):
                            st.session_state['assignments'] = all_assignments
                            utils.record_history(username, "Quest Abandoned", f"Abandoned quest: {quest_template.get('name')}", 0, USER_HISTORY_DIR)
                            st.warning(f"Quest '{quest_template.get('name')}' abandoned.")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to save quest abandonment.")
                    else:
                        st.error("Quest not found for abandonment.")
st.divider()

# --- Section 3: My Quests Awaiting Approval ---
st.header("📬 My Quests Awaiting Approval")
approval_quests = {
    assign_id: data for assign_id, data in user_assignments.items()
    if data.get('type') == 'quest' and data.get('status') == 'pending_approval'
}

if not approval_quests:
    st.info("You have no quests currently awaiting approval.")
else:
    for assign_id, assign_data in approval_quests.items():
        quest_template_id = assign_data.get('template_id')
        quest_template = quest_templates.get(quest_template_id, {})
        if not quest_template:
            st.warning(f"Could not find quest template for approval quest {assign_id}. Skipping.")
            continue

        with st.container(border=True):
            st.subheader(f"{quest_template.get('icon', '📬')} {quest_template.get('name', 'Unnamed Quest')}")
            st.markdown(f"**Description:** {quest_template.get('description', 'No description.')}")
            st.markdown(f"**Reward:** {quest_template.get('points', 0):,} Points")
            st.markdown(f"*Submitted on: {datetime.fromisoformat(assign_data.get('completed_on', datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M')}*")
            st.info("This quest is awaiting review by an admin. No further actions needed from you here.")
st.divider()

# --- Section 4: My Recently Completed Quests ---
st.header("🎉 My Recently Completed Quests")
completed_quests_all = {
    assign_id: data for assign_id, data in user_assignments.items()
    if data.get('type') == 'quest' and data.get('status') == 'completed'
}
# Sort by completion date, most recent first
sorted_completed_quests = sorted(completed_quests_all.items(), key=lambda item: item[1].get('final_completion_date', item[1].get('completed_on', '1970-01-01')), reverse=True)


if not sorted_completed_quests:
    st.info("You have not completed any quests yet. Keep up the great work on your active ones!")
else:
    st.markdown("Well done on completing these quests!")
    for assign_id, assign_data in sorted_completed_quests[:10]: # Show last 10
        quest_template_id = assign_data.get('template_id')
        quest_template = quest_templates.get(quest_template_id, {})
        if not quest_template:
            st.warning(f"Could not find quest template for completed quest {assign_id}. Skipping.")
            continue

        with st.container(border=True):
            st.subheader(f"{quest_template.get('icon', '✔️')} {quest_template.get('name', 'Unnamed Quest')}")
            completion_date_str = assign_data.get('final_completion_date', assign_data.get('completed_on'))
            completion_date_formatted = datetime.fromisoformat(completion_date_str).strftime('%Y-%m-%d %H:%M') if completion_date_str else "N/A"
            st.success(f"**Completed on:** {completion_date_formatted} | **Reward:** {quest_template.get('points', 0):,} Points")
            st.markdown(f"{quest_template.get('description', '')}")
