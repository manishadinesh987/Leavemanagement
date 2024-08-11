import sqlite3
from datetime import datetime
import yaml
from yaml.loader import SafeLoader
import bcrypt

def init_db_connection():
    """
        Initialize and return a connection to the SQLite database.

        Returns:
            sqlite3.Connection: Connection object to interact with the SQLite database.
        """
    conn = sqlite3.connect('leave_management.db')
    return conn

# Function to create tables (run this once)
def create_tables():
    """
     Create necessary tables in the database if they do not already exist.

     Tables:
         - users: Stores user information (name, email, password, role, manager).
         - leave_requests: Stores leave requests details (employee_id, manager, leave_type, comment, status).
     """
    conn = init_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            manager TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            manager TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            comment TEXT,
            status TEXT DEFAULT 'Waiting',
            application_date TEXT DEFAULT CURRENT_TIMESTAMP,
            decision_date TEXT,
            FOREIGN KEY (employee_id) REFERENCES users(id),
            FOREIGN KEY (manager) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()


# Save updated credentials to the YAML file
def save_config(config):
    with open('cred.yaml', 'w') as file:
        yaml.dump(config, file)

# Hash the password using bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')



# Load credentials from the YAML file
def load_config():
    """
        Load the YAML configuration file that contains user credentials and settings.

        Returns:
            dict: Configuration data loaded from the YAML file.
        """
    with open('cred.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

def update_leave_status(leave_id, status):
    #Update the status of a leave request in the database.

    conn = init_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE leave_requests 
        SET status=?, decision_date=? 
        WHERE id=?
    """, (status, datetime.now(), leave_id))
    conn.commit()
    conn.close()


def get_managers():
    """
        Retrieve the list of managers from the database.

        Returns:
            list: A list of manager names.
        """
    conn = init_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM users WHERE role = 'Manager'
    """)
    conn.commit()
    managers = cursor.fetchall()
    conn.close()
    managers = [a[0] for a in managers]
    return managers

# Insert a new user into the database
def insert_user(name, email, password, role, manager):
    conn = init_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (name, email, password, role, manager)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, email, hash_password(password), role, manager))
    conn.commit()
    conn.close()