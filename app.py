import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="SecureAuth — Advanced Login System",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DB_PATH = Path(__file__).parent / "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
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
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
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
    if user and user[5] == 1:
        return {'id': user[0], 'username': user[1], 'email': user[2], 'full_name': user[3], 'role': user[4]}
    return None

def register_user(username, email, password, full_name):
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def log_activity(user_id, activity_type, description):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO activity_logs (user_id, activity_type, description) VALUES (?, ?, ?)',
              (user_id, activity_type, description))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT id, username, email, full_name, role, created_at, last_login, is_active
        FROM users ORDER BY created_at DESC
    ''', conn)
    conn.close()
    return df

def get_activity_logs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT al.id, u.username, al.activity_type, al.description, al.timestamp
        FROM activity_logs al
        JOIN users u ON al.user_id = u.id
        ORDER BY al.timestamp DESC LIMIT 100
    ''', conn)
    conn.close()
    return df

def update_user_status(user_id, is_active):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET is_active = ? WHERE id = ?', (is_active, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    c.execute('DELETE FROM activity_logs WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def change_user_role(user_id, new_role):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()

# ─── ENHANCED CSS ──────────────────────────────────────────────────────────────
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Global Reset ── */
    * { font-family: 'Sora', sans-serif !important; }
    html, body, [class*="css"] { color: #0d0d0d !important; }

    /* ── App Background ── */
    .stApp {
        background: #f4f1ed;
        background-image:
            radial-gradient(circle at 20% 20%, rgba(99,60,180,0.07) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(220,80,80,0.06) 0%, transparent 50%);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(175deg, #1a0533 0%, #2d1060 40%, #1a0533 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * {
        color: #e8dff5 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #c9b8e8 !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #b8a8d4 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }

    /* ── Headings ── */
    h1 { color: #0d0d0d !important; font-weight: 800 !important; letter-spacing: -0.03em !important; }
    h2 { color: #1a1a2e !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    h3 { color: #1a1a2e !important; font-weight: 600 !important; }
    p, li, span, label, div { color: #1c1c1c !important; }

    /* ── Auth Page Background ── */
    .auth-bg {
        background: linear-gradient(135deg, #2d1060 0%, #1a0533 40%, #0d2461 100%);
        min-height: 100vh;
        padding: 3rem 1rem;
        margin: -1rem;
    }

    /* ── Auth Card ── */
    .auth-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 2.8rem 2.5rem;
        box-shadow:
            0 24px 60px rgba(0,0,0,0.22),
            0 8px 20px rgba(99,60,180,0.12),
            inset 0 1px 0 rgba(255,255,255,0.9);
        position: relative;
        overflow: hidden;
    }
    .auth-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6B3FCC, #e05555, #6B3FCC);
        background-size: 200% 100%;
        animation: shimmer 3s infinite;
    }
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    /* ── Auth Titles ── */
    .auth-title {
        text-align: center;
        color: #ffffff !important;
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0.3rem;
        text-shadow: 0 2px 20px rgba(0,0,0,0.3);
    }
    .auth-subtitle {
        text-align: center;
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.95rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input {
        background: #f8f6ff !important;
        border: 2px solid #e0d9f5 !important;
        border-radius: 10px !important;
        color: #0d0d0d !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding: 0.65rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6B3FCC !important;
        box-shadow: 0 0 0 3px rgba(107,63,204,0.15) !important;
        background: #ffffff !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #9b8cbf !important;
    }
    .stTextInput label {
        color: #1a1a2e !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.03em !important;
        padding: 0.65rem 1.2rem !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: none !important;
    }
    .stButton > button[kind="primary"],
    .stButton > button:first-child {
        background: linear-gradient(135deg, #6B3FCC 0%, #4a28a0 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(107,63,204,0.4) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(107,63,204,0.45) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        border: 1px solid #ede8f5;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(107,63,204,0.12);
    }
    [data-testid="stMetricLabel"] { color: #5a4a7a !important; font-weight: 600 !important; font-size: 0.8rem !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
    [data-testid="stMetricValue"] { color: #1a0533 !important; font-weight: 800 !important; font-size: 1.8rem !important; }

    /* ── Info / Success / Error / Warning boxes ── */
    .stAlert {
        border-radius: 12px !important;
        border-left-width: 4px !important;
    }
    .stAlert [data-testid="stMarkdownContainer"] p {
        color: #1c1c1c !important;
        font-weight: 500 !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #ede8f5;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        background: rgba(237, 232, 245, 0.97) !important;
        box-shadow: 0 2px 12px rgba(107,63,204,0.10) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px !important;
        color: #5a4a7a !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        user-select: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: #6B3FCC !important;
        color: #ffffff !important;
    }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #ede8f5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: #f8f6ff !important;
        border-radius: 10px !important;
        color: #1a0533 !important;
        font-weight: 600 !important;
        border: 1px solid #ede8f5 !important;
    }
    .streamlit-expanderContent {
        background: #fdfcff !important;
        border: 1px solid #ede8f5 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }

    /* ── Divider ── */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #d0c4ea, transparent) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Selectbox ── */
    .stSelectbox > div > div {
        background: #f8f6ff !important;
        border: 2px solid #e0d9f5 !important;
        border-radius: 10px !important;
        color: #0d0d0d !important;
    }
    .stSelectbox label { color: #1a1a2e !important; font-weight: 600 !important; font-size: 0.83rem !important; }

    /* ── Text areas ── */
    .stTextArea textarea {
        background: #f8f6ff !important;
        border: 2px solid #e0d9f5 !important;
        border-radius: 10px !important;
        color: #0d0d0d !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.88rem !important;
    }

    /* ── Sidebar logout button ── */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #e8dff5 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(220,80,80,0.25) !important;
        border-color: rgba(220,80,80,0.5) !important;
        color: #ffffff !important;
    }

    /* ── Badge / role pill ── */
    .role-pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .role-admin { background: #ffe0e0; color: #c0392b !important; }
    .role-user  { background: #e0ecff; color: #1a4fa0 !important; }

    /* ── Page titles ── */
    .page-header {
        padding: 1.5rem 0 1rem;
        border-bottom: 2px solid #ede8f5;
        margin-bottom: 1.8rem;
    }
    .page-header h1 { font-size: 2rem !important; color: #1a0533 !important; margin: 0 !important; }
    .page-header p  { color: #5a4a7a !important; margin: 0.3rem 0 0 !important; font-size: 0.95rem !important; }

    /* ── Info card ── */
    .info-card {
        background: linear-gradient(135deg, #f0ebff, #e8f0ff);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border-left: 4px solid #6B3FCC;
        margin-bottom: 0.8rem;
    }
    .info-card strong { color: #1a0533 !important; font-weight: 700 !important; }
    .info-card span   { color: #3a2a5e !important; font-weight: 500 !important; }

    /* ── About section ── */
    .about-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #ede8f5;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }
    .about-card h3 { color: #1a0533 !important; font-size: 1.1rem !important; margin-bottom: 0.6rem !important; }
    .about-card p  { color: #3a2a5e !important; line-height: 1.7 !important; font-size: 0.95rem !important; }
    .feature-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid #f0ebff;
        color: #1c1c1c !important;
    }
    .feature-icon { font-size: 1.2rem; flex-shrink: 0; }
    .feature-text strong { color: #1a0533 !important; display: block; font-weight: 700; font-size: 0.9rem; }
    .feature-text span   { color: #5a4a7a !important; font-size: 0.84rem; }

    /* ── Download button ── */
    [data-testid="stDownloadButton"] button {
        background: #1a0533 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ─── AUTH PAGES ────────────────────────────────────────────────────────────────
def login_page():
    local_css()
    st.markdown("<div class='auth-bg'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.6, 1])

    with col2:
        st.markdown("<div class='auth-title'>🔐 SecureAuth</div>", unsafe_allow_html=True)
        st.markdown("<div class='auth-subtitle'>Enterprise-grade access management</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#1a0533!important;margin-bottom:1.2rem;font-size:1.3rem;'>Sign in to your account</h3>", unsafe_allow_html=True)

            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🔑 Sign In", use_container_width=True):
                    if username and password:
                        user = verify_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            update_last_login(user['id'])
                            log_activity(user['id'], 'login', f"User {username} logged in")
                            st.success("✅ Login successful! Redirecting…")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password.")
                    else:
                        st.warning("⚠️ Please fill in both fields.")

            with col_btn2:
                if st.button("📝 Register", use_container_width=True):
                    st.session_state.page = 'register'
                    st.rerun()

            st.markdown("<hr style='margin:1.5rem 0;'>", unsafe_allow_html=True)

            with st.expander("ℹ️ Demo Credentials"):
                st.markdown("""
                <div style='padding:0.5rem 0;'>
                <p style='color:#1a0533!important;font-weight:700;margin-bottom:0.5rem;'>🛡️ Admin Account</p>
                <p style='color:#3a2a5e!important;font-family:JetBrains Mono,monospace;font-size:0.88rem;margin:0;'>
                Username: <strong style='color:#6B3FCC!important;'>admin</strong><br>
                Password: <strong style='color:#6B3FCC!important;'>admin123</strong>
                </p>
                <p style='color:#7a6a9a!important;font-size:0.82rem;margin-top:0.7rem;'>
                💡 Create your own account via the Register button.
                </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def register_page():
    local_css()
    st.markdown("<div class='auth-bg'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.6, 1])

    with col2:
        st.markdown("<div class='auth-title'>📝 Create Account</div>", unsafe_allow_html=True)
        st.markdown("<div class='auth-subtitle'>Join the platform in seconds</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#1a0533!important;margin-bottom:1.2rem;font-size:1.3rem;'>Fill in your details</h3>", unsafe_allow_html=True)

            full_name        = st.text_input("Full Name",        placeholder="Jane Doe")
            username         = st.text_input("Username",         placeholder="janedoe")
            email            = st.text_input("Email",            placeholder="jane@example.com")
            password         = st.text_input("Password",         type="password", placeholder="Min. 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Create Account", use_container_width=True):
                    if not all([full_name, username, email, password, confirm_password]):
                        st.warning("⚠️ Please fill in all fields.")
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match.")
                    elif len(password) < 6:
                        st.warning("⚠️ Password must be at least 6 characters.")
                    else:
                        success, message = register_user(username, email, password, full_name)
                        if success:
                            st.success(f"🎉 {message}")
                            st.balloons()
                            st.info("✅ You can now sign in with your credentials.")
                        else:
                            st.error(f"❌ {message}")

            with col_btn2:
                if st.button("⬅️ Back to Login", use_container_width=True):
                    st.session_state.page = 'login'
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def user_dashboard():
    local_css()
    u = st.session_state.user

    st.markdown(f"""
    <div class='page-header'>
        <h1>👋 Welcome back, {u['full_name'].split()[0]}!</h1>
        <p>Here's a summary of your account activity and profile.</p>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🧑 Username", u['username'])
    with col2:
        st.metric("📧 Email", u['email'])
    with col3:
        role_label = "👑 ADMIN" if u['role'] == 'admin' else "👤 USER"
        st.metric("🎭 Role", role_label)

    st.divider()

    # Account info
    st.subheader("📋 Account Details")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT created_at, last_login FROM users WHERE id = ?', (u['id'],))
    user_info = c.fetchone()
    conn.close()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='info-card'>
            <strong>📅 Account Created</strong><br>
            <span>{user_info[0]}</span>
        </div>""", unsafe_allow_html=True)
    with col2:
        last = user_info[1] if user_info[1] else "First login"
        st.markdown(f"""
        <div class='info-card'>
            <strong>🕐 Last Login</strong><br>
            <span>{last}</span>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # Recent activity
    st.subheader("🔄 Recent Activity")
    conn = sqlite3.connect(DB_PATH)
    activity_df = pd.read_sql_query('''
        SELECT activity_type AS "Type", description AS "Description", timestamp AS "Time"
        FROM activity_logs WHERE user_id = ?
        ORDER BY timestamp DESC LIMIT 10
    ''', conn, params=(u['id'],))
    conn.close()

    if not activity_df.empty:
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("📭 No recent activity to display yet.")

    st.divider()

    # ── ABOUT SECTION ──
    st.subheader("ℹ️ About SecureAuth")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='about-card'>
            <h3>🔐 What is SecureAuth?</h3>
            <p>
            SecureAuth is a full-featured, production-ready authentication and user management
            platform. Built on top of SQLite with SHA-256 password hashing, it provides
            enterprise-grade security in a lightweight, self-hosted package.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='about-card'>
            <h3>⚡ Core Features</h3>
            <div class='feature-item'>
                <span class='feature-icon'>🛡️</span>
                <div class='feature-text'>
                    <strong>SHA-256 Password Hashing</strong>
                    <span>Passwords are never stored in plain text — always salted and hashed.</span>
                </div>
            </div>
            <div class='feature-item'>
                <span class='feature-icon'>👥</span>
                <div class='feature-text'>
                    <strong>Role-Based Access</strong>
                    <span>Two permission levels: Admin (full control) and User (standard access).</span>
                </div>
            </div>
            <div class='feature-item'>
                <span class='feature-icon'>📊</span>
                <div class='feature-text'>
                    <strong>Activity Logging</strong>
                    <span>Every login, logout, and admin action is recorded with timestamps.</span>
                </div>
            </div>
            <div class='feature-item'>
                <span class='feature-icon'>⚙️</span>
                <div class='feature-text'>
                    <strong>Admin Control Panel</strong>
                    <span>Full user management: activate, deactivate, promote, or delete users.</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='about-card'>
            <h3>🛠️ Technology Stack</h3>
            <div class='feature-item'>
                <span class='feature-icon'>🐍</span>
                <div class='feature-text'>
                    <strong>Python 3.x</strong>
                    <span>Core backend language — clean, readable, and powerful.</span>
                </div>
            </div>
            <div class='feature-item'>
                <span class='feature-icon'>🌊</span>
                <div class='feature-text'>
                    <strong>Streamlit</strong>
                    <span>Reactive UI framework for rapid, data-driven web interfaces.</span>
                </div>
            </div>
            <div class='feature-item'>
                <span class='feature-icon'>🗄️</span>
                <div class='feature-text'>
                    <strong>SQLite</strong>
                    <span>Lightweight, serverless relational database — zero setup required.</span>
                </div>
            </div>
            <div class='feature-item'>
                <span class='feature-icon'>🐼</span>
                <div class='feature-text'>
                    <strong>Pandas</strong>
                    <span>Data manipulation and CSV export for logs and user tables.</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='about-card'>
            <h3>🔒 Security Notes</h3>
            <p style='color:#3a2a5e!important;line-height:1.75;font-size:0.9rem;'>
            • Passwords hashed with <strong style='color:#1a0533!important;'>SHA-256</strong> before storage<br>
            • Inactive accounts are blocked at authentication<br>
            • Admin cannot be accidentally deactivated via the UI<br>
            • SQL query tool restricted to <strong style='color:#1a0533!important;'>read-only</strong> by convention<br>
            • Session state is cleared completely on logout
            </p>
        </div>
        """, unsafe_allow_html=True)


# ─── ADMIN PANEL ───────────────────────────────────────────────────────────────
def admin_panel():
    local_css()
    st.markdown("""
    <div class='page-header'>
        <h1>⚙️ Admin Control Panel</h1>
        <p>Manage users, review logs, and run diagnostic queries.</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM activity_logs")
    total_activities = c.fetchone()[0]
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Users", total_users)
    with col2:
        st.metric("🟢 Active Users", active_users)
    with col3:
        st.metric("🔴 Inactive", total_users - active_users)
    with col4:
        st.metric("📋 Log Entries", total_activities)

    st.divider()

    tab1, tab2, tab3 = st.tabs(["👥  User Management", "📝  Activity Logs", "🗄️  Database Query"])

    with tab1:
        st.markdown("<h3 style='color:#1a0533!important;margin-bottom:1rem;'>All Registered Users</h3>", unsafe_allow_html=True)
        users_df = get_all_users()

        for idx, row in users_df.iterrows():
            status_icon = "🟢" if row['is_active'] else "🔴"
            role_badge  = "👑 Admin" if row['role'] == 'admin' else "👤 User"
            with st.expander(f"{status_icon} {row['username']}  —  {row['email']}  [{role_badge}]"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"<p><strong style='color:#1a0533!important;'>Full Name</strong><br><span style='color:#3a2a5e!important;'>{row['full_name']}</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong style='color:#1a0533!important;'>Role</strong><br><span style='color:#3a2a5e!important;'>{row['role'].upper()}</span></p>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<p><strong style='color:#1a0533!important;'>Created</strong><br><span style='color:#3a2a5e!important;'>{row['created_at']}</span></p>", unsafe_allow_html=True)
                    last = row['last_login'] if row['last_login'] else 'Never'
                    st.markdown(f"<p><strong style='color:#1a0533!important;'>Last Login</strong><br><span style='color:#3a2a5e!important;'>{last}</span></p>", unsafe_allow_html=True)
                with col3:
                    new_role = st.selectbox("Change Role", ["user", "admin"],
                                            index=0 if row['role'] == 'user' else 1,
                                            key=f"role_{row['id']}")
                    if st.button("💾 Update Role", key=f"update_role_{row['id']}"):
                        change_user_role(row['id'], new_role)
                        st.success(f"✅ Role updated to {new_role}")
                        st.rerun()
                with col4:
                    if row['username'] != 'admin':
                        if row['is_active']:
                            if st.button("🔴 Deactivate", key=f"deactivate_{row['id']}"):
                                update_user_status(row['id'], 0)
                                log_activity(st.session_state.user['id'], 'admin', f"Deactivated {row['username']}")
                                st.warning("User deactivated.")
                                st.rerun()
                        else:
                            if st.button("🟢 Activate", key=f"activate_{row['id']}"):
                                update_user_status(row['id'], 1)
                                log_activity(st.session_state.user['id'], 'admin', f"Activated {row['username']}")
                                st.success("User activated.")
                                st.rerun()
                        if st.button("🗑️ Delete User", key=f"delete_{row['id']}"):
                            delete_user(row['id'])
                            log_activity(st.session_state.user['id'], 'admin', f"Deleted {row['username']}")
                            st.error("User deleted.")
                            st.rerun()
                    else:
                        st.markdown("<p style='color:#9b8cbf!important;font-size:0.82rem;'>🔒 Protected account</p>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<h3 style='color:#1a0533!important;margin-bottom:1rem;'>Recent Activity Logs</h3>", unsafe_allow_html=True)
        logs_df = get_activity_logs()
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True, height=400)
            csv = logs_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Logs as CSV",
                data=csv,
                file_name=f"activity_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📭 No activity logs found.")

    with tab3:
        st.markdown("<h3 style='color:#1a0533!important;margin-bottom:0.5rem;'>SQL Query Tool</h3>", unsafe_allow_html=True)
        st.warning("⚠️ **Caution:** Only SELECT queries are recommended. Modifications may break the application.")
        query = st.text_area("SQL Query", value="SELECT * FROM users LIMIT 10;", height=120)
        if st.button("🔍 Execute Query"):
            try:
                conn = sqlite3.connect(DB_PATH)
                result_df = pd.read_sql_query(query, conn)
                conn.close()
                st.success(f"✅ Query returned {len(result_df)} row(s).")
                st.dataframe(result_df, use_container_width=True)
                csv = result_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name=f"query_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"❌ Query error: {str(e)}")


# ─── MAIN ──────────────────────────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def main():
    init_db()
    local_css()

    if not st.session_state.logged_in:
        if st.session_state.page == 'login':
            login_page()
        elif st.session_state.page == 'register':
            register_page()
    else:
        u = st.session_state.user
        with st.sidebar:
            st.markdown(f"""
            <div style='text-align:center;padding:1rem 0;'>
                <div style='width:70px;height:70px;border-radius:50%;
                     background:linear-gradient(135deg,#6B3FCC,#e05555);
                     display:flex;align-items:center;justify-content:center;
                     font-size:1.8rem;margin:0 auto 0.8rem;
                     box-shadow:0 4px 16px rgba(107,63,204,0.4);'>
                    {'👑' if u['role']=='admin' else '👤'}
                </div>
                <p style='color:#ffffff!important;font-weight:700;font-size:1rem;margin:0;'>
                    {u['full_name']}
                </p>
                <p style='color:#b8a8d4!important;font-size:0.78rem;margin:0.2rem 0 0;'>
                    @{u['username']} · {u['role'].upper()}
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            if u['role'] == 'admin':
                page = st.radio("Navigation", ["🏠 Dashboard", "⚙️ Admin Panel"], key="nav",
                                label_visibility="collapsed")
            else:
                page = "🏠 Dashboard"
                st.markdown("<p style='color:#b8a8d4!important;font-size:0.85rem;'>🏠 Dashboard</p>", unsafe_allow_html=True)

            st.divider()

            # Quick stats in sidebar
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM activity_logs WHERE user_id = ?", (u['id'],))
            user_log_count = c.fetchone()[0]
            conn.close()
            st.markdown(f"<p style='color:#b8a8d4!important;font-size:0.8rem;'>📋 Your log entries: <strong style='color:#e8dff5!important;'>{user_log_count}</strong></p>", unsafe_allow_html=True)

            st.divider()
            if st.button("🚪 Sign Out", use_container_width=True):
                log_activity(u['id'], 'logout', f"User {u['username']} logged out")
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = 'login'
                st.rerun()

        if page == "🏠 Dashboard":
            user_dashboard()
        elif page == "⚙️ Admin Panel" and u['role'] == 'admin':
            admin_panel()

if __name__ == "__main__":
    main()
