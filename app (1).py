import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Advanced Login System",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DB_PATH = Path(__file__).parent / "users.db"

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Create activity logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type TEXT,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user if not exists
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_password = hash_password("admin123")
        c.execute('''
            INSERT INTO users (username, email, password, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ("admin", "admin@system.com", admin_password, "System Administrator", "admin"))
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    hashed_password = hash_password(password)
    c.execute('''
        SELECT id, username, email, full_name, role, is_active 
        FROM users 
        WHERE username = ? AND password = ?
    ''', (username, hashed_password))
    
    user = c.fetchone()
    conn.close()
    
    if user and user[5] == 1:  # is_active check
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'full_name': user[3],
            'role': user[4]
        }
    return None

def register_user(username, email, password, full_name):
    """Register a new user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        hashed_password = hash_password(password)
        c.execute('''
            INSERT INTO users (username, email, password, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, hashed_password, full_name, "user"))
        
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already exists!"
        elif "email" in str(e):
            return False, "Email already registered!"
        return False, "Registration failed!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def update_last_login(user_id):
    """Update user's last login time"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET last_login = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def log_activity(user_id, activity_type, description):
    """Log user activity"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO activity_logs (user_id, activity_type, description)
        VALUES (?, ?, ?)
    ''', (user_id, activity_type, description))
    conn.commit()
    conn.close()

def get_all_users():
    """Get all users from database"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT id, username, email, full_name, role, 
               created_at, last_login, is_active
        FROM users
        ORDER BY created_at DESC
    ''', conn)
    conn.close()
    return df

def get_activity_logs():
    """Get activity logs"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT al.id, u.username, al.activity_type, 
               al.description, al.timestamp
        FROM activity_logs al
        JOIN users u ON al.user_id = u.id
        ORDER BY al.timestamp DESC
        LIMIT 100
    ''', conn)
    conn.close()
    return df

def update_user_status(user_id, is_active):
    """Activate or deactivate user"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET is_active = ? WHERE id = ?', (is_active, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    """Delete user from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    c.execute('DELETE FROM activity_logs WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def change_user_role(user_id, new_role):
    """Change user role"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()

# Custom CSS
def local_css():
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .stTextInput>div>div>input {
            background-color: #f0f2f6;
        }
        .login-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .success-message {
            padding: 1rem;
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            border-radius: 4px;
            margin: 1rem 0;
        }
        .error-message {
            padding: 1rem;
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            border-radius: 4px;
            margin: 1rem 0;
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def login_page():
    """Display login page"""
    local_css()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: white;'>🔐 Welcome Back</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white;'>Login to your account</p>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            
            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🔑 Login", use_container_width=True):
                    if username and password:
                        user = verify_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            update_last_login(user['id'])
                            log_activity(user['id'], 'login', f"User {username} logged in")
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password!")
                    else:
                        st.warning("Please enter both username and password!")
            
            with col_btn2:
                if st.button("📝 Register", use_container_width=True):
                    st.session_state.page = 'register'
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Demo credentials info
            with st.expander("ℹ️ Demo Credentials"):
                st.info("""
                **Admin Account:**
                - Username: `admin`
                - Password: `admin123`
                
                **Note:** You can create your own account using the Register button.
                """)

def register_page():
    """Display registration page"""
    local_css()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: white;'>📝 Create Account</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white;'>Register a new account</p>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            
            full_name = st.text_input("Full Name", placeholder="Enter your full name")
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Choose a strong password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✅ Register", use_container_width=True):
                    if not all([full_name, username, email, password, confirm_password]):
                        st.warning("Please fill in all fields!")
                    elif password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(password) < 6:
                        st.warning("Password must be at least 6 characters!")
                    else:
                        success, message = register_user(username, email, password, full_name)
                        if success:
                            st.success(message)
                            st.balloons()
                            st.info("You can now login with your credentials!")
                        else:
                            st.error(message)
            
            with col_btn2:
                if st.button("⬅️ Back to Login", use_container_width=True):
                    st.session_state.page = 'login'
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

def user_dashboard():
    """Display user dashboard"""
    st.title(f"👋 Welcome, {st.session_state.user['full_name']}!")
    
    # User info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Username", st.session_state.user['username'])
    with col2:
        st.metric("Email", st.session_state.user['email'])
    with col3:
        st.metric("Role", st.session_state.user['role'].upper())
    
    st.divider()
    
    # User activities section
    st.subheader("📊 Your Account Information")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT created_at, last_login 
        FROM users 
        WHERE id = ?
    ''', (st.session_state.user['id'],))
    user_info = c.fetchone()
    conn.close()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Account Created:** {user_info[0]}")
    with col2:
        st.info(f"**Last Login:** {user_info[1] if user_info[1] else 'First login'}")
    
    # Recent activity
    st.subheader("🔄 Your Recent Activity")
    conn = sqlite3.connect(DB_PATH)
    activity_df = pd.read_sql_query('''
        SELECT activity_type, description, timestamp
        FROM activity_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', conn, params=(st.session_state.user['id'],))
    conn.close()
    
    if not activity_df.empty:
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("No recent activity to display.")

def admin_panel():
    """Display admin panel"""
    st.title("⚙️ Admin Panel")
    
    # Statistics
    st.subheader("📊 System Statistics")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM activity_logs")
    total_activities = c.fetchone()[0]
    
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Users", total_users, delta="All registered")
    with col2:
        st.metric("Active Users", active_users, delta=f"{active_users}/{total_users}")
    with col3:
        st.metric("Total Activities", total_activities, delta="Logged")
    
    st.divider()
    
    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "📝 Activity Logs", "🗄️ Database Query"])
    
    with tab1:
        st.subheader("User Management")
        
        # Get all users
        users_df = get_all_users()
        
        # Display users with action buttons
        for idx, row in users_df.iterrows():
            with st.expander(f"👤 {row['username']} - {row['email']}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**Full Name:** {row['full_name']}")
                    st.write(f"**Role:** {row['role']}")
                
                with col2:
                    st.write(f"**Created:** {row['created_at']}")
                    st.write(f"**Last Login:** {row['last_login'] if row['last_login'] else 'Never'}")
                
                with col3:
                    status = "🟢 Active" if row['is_active'] else "🔴 Inactive"
                    st.write(f"**Status:** {status}")
                    
                    # Change role
                    new_role = st.selectbox(
                        "Change Role",
                        ["user", "admin"],
                        index=0 if row['role'] == 'user' else 1,
                        key=f"role_{row['id']}"
                    )
                    if st.button("Update Role", key=f"update_role_{row['id']}"):
                        change_user_role(row['id'], new_role)
                        st.success(f"Role updated to {new_role}")
                        st.rerun()
                
                with col4:
                    # Toggle active status
                    if row['username'] != 'admin':  # Prevent disabling admin
                        if row['is_active']:
                            if st.button("🔴 Deactivate", key=f"deactivate_{row['id']}"):
                                update_user_status(row['id'], 0)
                                log_activity(st.session_state.user['id'], 'admin', f"Deactivated user {row['username']}")
                                st.warning("User deactivated")
                                st.rerun()
                        else:
                            if st.button("🟢 Activate", key=f"activate_{row['id']}"):
                                update_user_status(row['id'], 1)
                                log_activity(st.session_state.user['id'], 'admin', f"Activated user {row['username']}")
                                st.success("User activated")
                                st.rerun()
                        
                        # Delete user
                        if st.button("🗑️ Delete User", key=f"delete_{row['id']}"):
                            delete_user(row['id'])
                            log_activity(st.session_state.user['id'], 'admin', f"Deleted user {row['username']}")
                            st.error("User deleted")
                            st.rerun()
    
    with tab2:
        st.subheader("Activity Logs")
        
        # Get activity logs
        logs_df = get_activity_logs()
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True, height=400)
            
            # Download button
            csv = logs_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Logs (CSV)",
                data=csv,
                file_name=f"activity_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No activity logs found.")
    
    with tab3:
        st.subheader("Database Query Tool")
        st.warning("⚠️ Use with caution! Only SELECT queries are recommended.")
        
        query = st.text_area(
            "Enter SQL Query",
            value="SELECT * FROM users LIMIT 10;",
            height=100
        )
        
        if st.button("🔍 Execute Query"):
            try:
                conn = sqlite3.connect(DB_PATH)
                result_df = pd.read_sql_query(query, conn)
                conn.close()
                
                st.success("Query executed successfully!")
                st.dataframe(result_df, use_container_width=True)
                
                # Download results
                csv = result_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results (CSV)",
                    data=csv,
                    file_name=f"query_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error executing query: {str(e)}")

def main():
    """Main application logic"""
    # Initialize database
    init_db()
    
    # Routing
    if not st.session_state.logged_in:
        if st.session_state.page == 'login':
            login_page()
        elif st.session_state.page == 'register':
            register_page()
    else:
        # Sidebar for logged-in users
        with st.sidebar:
            st.image("https://via.placeholder.com/150x150.png?text=👤", width=150)
            st.title(f"👋 {st.session_state.user['username']}")
            st.caption(f"Role: {st.session_state.user['role'].upper()}")
            
            st.divider()
            
            # Navigation
            if st.session_state.user['role'] == 'admin':
                page = st.radio(
                    "Navigation",
                    ["🏠 Dashboard", "⚙️ Admin Panel"],
                    key="nav"
                )
            else:
                page = "🏠 Dashboard"
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True):
                log_activity(st.session_state.user['id'], 'logout', f"User {st.session_state.user['username']} logged out")
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = 'login'
                st.rerun()
        
        # Display selected page
        if page == "🏠 Dashboard":
            user_dashboard()
        elif page == "⚙️ Admin Panel" and st.session_state.user['role'] == 'admin':
            admin_panel()

if __name__ == "__main__":
    main()
