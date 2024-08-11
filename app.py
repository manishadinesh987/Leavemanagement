import streamlit as st
import signup_page
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from utils import init_db_connection, update_leave_status, create_tables, load_config
import pandas as pd
from datetime import datetime
import os


def login_page(authenticator):
    """
       Handle user login using Streamlit Authenticator.

       Args:
           authenticator (stauth.Authenticate): The authenticator object to manage login.

       Updates:
           st.session_state["authentication_status"]: Tracks the login status.
           st.session_state["username"]: Stores the logged-in username.
           st.session_state["role"]: Stores the role of the logged-in user.
       """
    name, authentication_status, username = authenticator.login(key='Login')

    if authentication_status:
        st.session_state["authentication_status"] = True
        st.success(f"Welcome {name}!")
        # Retrieve user role
        conn = init_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE name=?", (username,))
        role = cursor.fetchone()[0]
        conn.close()
        st.session_state["username"] = username
        st.session_state["role"] = role
        st.rerun()

    elif authentication_status is False:
        st.error('Username/password is incorrect')
    elif authentication_status is None:
        st.warning('Please enter your username and password')

def set_logout(authenticator):
    #Add a logout button to the sidebar and handle the logout process.

    if st.sidebar.button("Logout"):
        authenticator.logout("Logout", "sidebar")
        # Clear session state immediately
        st.session_state.clear()
        st.rerun()

def employee_page(authenticator):
    #Display the Employee Dashboard where employees can apply for leave and view their leave requests.
    username = st.session_state.username
    role = st.session_state.role

    # authenticator.logout("Logout", "sidebar")
    set_logout(authenticator)

    st.subheader("Employee Dashboard")
    st.text(f"Logged in as: {username}")

    # Fetch user details
    conn = init_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, manager FROM users WHERE name=?", (username,))
    user_id, manager = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM leave_requests WHERE employee_id=? AND status='Waiting'", (user_id,))
    current_leave_count = cursor.fetchone()[0]
    if current_leave_count <10:
        # Leave Application Form
        st.write("Apply for Leave")

        leave_type = st.selectbox("Leave Type", ["Personal", "Sick", "Official"])
        application_date = st.date_input("Select a date", value=datetime.today())
        comment = st.text_area("Reason for Leave")
        if st.button("Apply for Leave"):
            cursor.execute("""
                INSERT INTO leave_requests (employee_id, manager, leave_type, application_date, comment) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, manager, leave_type, application_date, comment))
            conn.commit()
            st.success("Leave application submitted successfully!")
            st.warning(f"Remaining Leaves: {10 - current_leave_count-1}")

    else:
        st.warning("You have reached maximum Leave requests : 10")

    # Display Leave Requests
    st.write("Your Leave Requests")
    cursor.execute("SELECT manager,leave_type,comment,status,application_date FROM leave_requests WHERE employee_id=?", (user_id,))
    leave_requests = cursor.fetchall()
    conn.close()
    if leave_requests:
        df = pd.DataFrame(leave_requests)
        df.columns = ['manager', 'leave_type', 'comment', 'status', 'application_date']
        st.table(df)

def manager_page(authenticator):
    # Display the Manager Dashboard where managers can view and approve/reject leave requests from their employees.
    st.markdown("""
            <style>
            .stButton button {
                padding: 0px 10px !important;

            }
            </style>
        """, unsafe_allow_html=True)
    username = st.session_state.username
    role = st.session_state.role
    set_logout(authenticator)
    st.subheader("Manager Dashboard")
    st.text(f"Logged in as: {username}")

    # Fetch manager details
    conn = init_db_connection()
    cursor = conn.cursor()

    # Display Leave Requests for Approval
    st.write("Leave Requests from Your Employees")
    cursor.execute("""SELECT lr.id, u.name, lr.application_date, lr.leave_type, lr.comment, lr.status
                FROM leave_requests lr
                JOIN users u ON lr.employee_id = u.id
                WHERE lr.manager = ? AND lr.status = 'Waiting';""", (username,))
    leave_requests = cursor.fetchall()
    conn.close()
    if leave_requests:
        df = pd.DataFrame(leave_requests)
        df.columns = ['Leave id', 'Name', 'Application Date', 'Leave type', 'Comment', 'Status']
        # st.write(df.columns)

        # Add approval/rejection buttons for each leave request
        for index, row in df.iterrows():
            # st.dataframe(row)
            proportions = [3] * (len(row)+2)
            proportions[-1] = 4     # reject field
            proportions[-2] = 4     # accept field
            proportions[2] = 5     # date field
            cols = st.columns(proportions)
            for i, val in enumerate(row):
                if i != 0:
                    cols[i].write(val)

            # Approval buttons
            if cols[-2].button("Approve", key=f"approve_{index}", use_container_width=True):
                update_leave_status(row[0], "Approved")
                st.success(f"Approved leave for {row[1]}")
                st.rerun()  # Refresh the app to reflect changes

            # Approval buttons
            if cols[-1].button("Reject", key=f"reject_{index}"):
                update_leave_status(row[0], "Rejected")
                st.success(f"Rejected leave for {row[1]}")
                st.rerun()  # Refresh the app to reflect changes
        # st.table(df)
    else:
        st.success("No Waiting leave requests")

    # Display Leave Requests
    st.write("Leave Requests History")
    conn = init_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT u.name, lr.application_date, lr.leave_type, lr.comment, lr.status
                   FROM leave_requests lr
                   JOIN users u ON lr.employee_id = u.id
                   WHERE lr.manager = ?""", (username,))
    leave_requests = cursor.fetchall()
    conn.close()
    if leave_requests:
        df = pd.DataFrame(leave_requests)
        df.columns = ['Name', 'Application Date', 'Leave type', 'Comment', 'Status']
        st.table(df)
def homepage():
    """
        Display the homepage of the Leave Management System.

        Provides a welcome message, an image, and a button to navigate to the login/signup page.
        """
    # Add a heading with good contrast
    st.markdown("<h1 style='text-align: center; color: #212121;'>Welcome to the Leave Management System</h1>", unsafe_allow_html=True)

    st.image("images/3.svg", use_column_width=True)

    # Add space between elements
    st.write("")
    st.write("")

    # Center the login/signup button
    if st.button("Login/Signup"):
        st.session_state["is_home"] = False
        st.rerun()

# Main app
def main():
    """
       The main function of the Streamlit application.

       It handles the initial setup, database creation, and navigation between different pages.
       """
    #st.title("Leave Management System")
    st.markdown("""
              <style>
              body {
                  background-color: powderblue;
              }
              .main {
                  background-color: powderblue;
                  padding: 2rem;
                  border-radius: 10px;
                  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
              }
              .stButton button {
                  background-color: #6200ea;
                  color: white;
                  border: none;
                  border-radius: 4px;
                  padding: 0.5rem 2rem;
                  margin: 1rem 0;
                  font-size: 1rem;
                  font-weight: bold;
                  text-transform: uppercase;
                  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
                  transition: background-color 0.3s ease;
                  display: block;
                  margin-left: auto;
                  margin-right: auto;
              }
              .stButton button:hover {
                  background-color: #3700b3;
              }

              </style>
          """, unsafe_allow_html=True)

    # Create tables if they don't exist
    create_tables()
    if "is_home" not in st.session_state:
        st.session_state["is_home"] = True
    if st.session_state.get("is_home") and st.session_state["is_home"]:
        homepage()
        st.session_state["is_home"] = False
        st.stop()

    menu = st.sidebar.selectbox("Menu", ["Login", "Signup"])
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None
    config = load_config()
    authenticator = stauth.Authenticate(
        config['credentials'],
        cookie_name=None,  # This disables cookie storage
        cookie_expiry_days=0,
        cookie_key=None
    )
    if st.session_state["authentication_status"] and st.session_state.get("role"):
        role = st.session_state["role"]
        username = st.session_state["username"]
        if role == "Employee":
            employee_page(authenticator)
        elif role == "Manager":
            manager_page(authenticator)
    else:
        if menu == "Login":
            login_page(authenticator)
        elif menu == "Signup":
            signup_page.signup_page()




if __name__ == '__main__':
    main()
