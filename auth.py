# auth.py

import streamlit as st
import streamlit_authenticator as stauth
# Make sure you have the specific version installed:
# pip install streamlit-authenticator~=0.3.3
import yaml
from yaml.loader import SafeLoader

CONFIG_FILE = 'config.yaml'

def load_config(filename=CONFIG_FILE):
    """Loads and validates the configuration from the YAML file."""
    try:
        with open(filename) as file:
            config = yaml.load(file, Loader=SafeLoader)
        if not config: # Handle empty config file
             raise ValueError("Config file is empty.")
        if 'credentials' not in config or 'cookie' not in config:
             raise ValueError("Config file missing required sections ('credentials', 'cookie')")
        # Ensure roles and children lists exist (or default) for validation robustness
        for un, data in config.get('credentials', {}).get('usernames', {}).items():
            data.setdefault('role', None) # Ensure role exists, defaults to None if missing
            if data.get('role') == 'parent':
                data.setdefault('children', []) # Ensure children list exists for parents
        return config
    except FileNotFoundError:
        st.error(f"❌ **Error:** `{filename}` not found. Please create it.")
        st.stop()
    except (yaml.YAMLError, ValueError) as e:
        st.error(f"❌ **Error:** Could not parse `{filename}`: {e}")
        st.stop()
    except Exception as e: # Catch unexpected errors during loading
        st.error(f"❌ **An unexpected error occurred loading config:** {e}")
        st.stop()


def authenticate():
    """
    Handles the authentication process.
    Loads config, initializes authenticator, performs login, and stores
    relevant info (config, authenticator, role) in session state.

    Returns:
        tuple: (name, authentication_status, username) from authenticator.login()
    """
    # Load config into session state if not already there
    if 'config' not in st.session_state:
        st.session_state['config'] = load_config()
    config = st.session_state['config']

    # Initialize authenticator and store in session state if not already there
    if 'authenticator' not in st.session_state:
        try:
            st.session_state['authenticator'] = stauth.Authenticate(
                config['credentials'],
                config['cookie']['name'],
                config['cookie']['key'],
                config['cookie']['expiry_days'],
                config['preauthorized']
            )
        except Exception as e:
            st.error(f"❌ **Error initializing authenticator:** {e}")
            st.error("Please check your config.yaml structure, especially credentials and cookie sections.")
            st.stop()

    authenticator = st.session_state['authenticator']

    # Perform login
    name, authentication_status, username = authenticator.login()

    # If login is successful, determine and store the user's role
    if authentication_status:
        try:
            # Use .get() for safer access in case username somehow doesn't exist after login
            user_data = config.get('credentials', {}).get('usernames', {}).get(username, {})
            st.session_state['role'] = user_data.get('role')
            # Add an extra check if role wasn't found/set in config
            if st.session_state['role'] is None:
                 st.warning(f"Role not defined for user '{username}' in {CONFIG_FILE}. Assuming default behavior.")
                 # Decide default behavior or stop execution if role is mandatory
                 # st.stop() # Or assign a default role
        except Exception as e: # Catch unexpected errors during role lookup
            st.error(f"An unexpected error occurred determining user role: {e}")
            st.session_state['role'] = None # Default to None on error
    else:
        # Clear role if authentication fails or is not yet attempted
        if 'role' in st.session_state:
            del st.session_state['role']

    return name, authentication_status, username