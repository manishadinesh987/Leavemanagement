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

    with st.form("signup_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Employee", "Manager"], key='role')

        managers = get_managers()
        managers.insert(0, None)
        manager = st.selectbox("Manager (if applicable)", managers)

        submit_button = st.form_submit_button("Sign Up")

        if submit_button:
            if role == "Employee" and not manager:
                st.error("Please enter your manager's name.")
            else:
                try:
                    insert_user(name, email, password, role, manager)
                    hashed_password = hash_password(password)
                    config = load_config()

                    config['credentials']['usernames'][name] = {
                        'email': email,
                        'name': name,
                        'password': hashed_password,
                        'role': role
                    }
                    save_config(config)
                    st.success("Sign up successful!")
                except sqlite3.IntegrityError:
                    st.error("Email already exists. Please use a different email.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
