import streamlit as st
import sqlite3
from utils import get_managers, insert_user, load_config, hash_password, save_config


def signup_page():
    """
    Display the sign-up page where new users can create an account.

    The form allows users to input their name, email, password, and select a role
    (Employee or Manager). If the role is Employee, they must select a manager
    from a dropdown list.
    """
    st.title("Sign Up")

    # Select role outside the form
    if 'role' not in st.session_state:
        st.session_state['role'] = 'Employee'

    role = st.selectbox("Role", ["Employee", "Manager"], key='role')

    with st.form("signup_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        managers = get_managers()
        managers.insert(0, "Select a Manager")

        # Disable the Manager dropdown when the role is "Manager"
        manager = st.selectbox(
            "Manager",
            managers,
            index=0,
            disabled=st.session_state['role'] == "Manager"  # Disable dropdown if role is "Manager"
        )

        submit_button = st.form_submit_button("Sign Up")

        if submit_button:
            # Validation
            if not name:
                st.error("Please enter your name.")
            elif not email:
                st.error("Please enter your email.")
            elif not password:
                st.error("Please enter your password.")
            elif st.session_state['role'] == "Employee" and (not manager or manager == "Select a Manager"):
                st.error("Please select a manager.")
            elif st.session_state['role'] == "Manager" and manager != "Select a Manager":
                st.error("Manager field should be None for Manager role.")
            else:
                try:
                    hashed_password = hash_password(password)
                    insert_user(name, email, hashed_password, st.session_state['role'],
                                None if st.session_state['role'] == "Manager" else manager)

                    config = load_config()
                    config['credentials']['usernames'][name] = {
                        'email': email,
                        'name': name,
                        'password': hashed_password,
                        'role': st.session_state['role']
                    }
                    save_config(config)
                    st.success("Sign up successful!")
                except sqlite3.IntegrityError:
                    st.error("Email already exists. Please use a different email.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

