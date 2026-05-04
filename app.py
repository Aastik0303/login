import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="SecureAuth",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = Path(__file__).parent / "users.db"

# ── DB Functions ────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity_type TEXT,
        description TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute('INSERT INTO users (username, email, password, full_name, role) VALUES (?,?,?,?,?)',
                  ("admin", "admin@system.com", hash_password("admin123"), "System Administrator", "admin"))
    conn.commit(); conn.close()

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute('SELECT id,username,email,full_name,role,is_active FROM users WHERE username=? AND password=?',
              (username, hash_password(password)))
    u = c.fetchone(); conn.close()
    if u and u[5] == 1:
        return {'id':u[0],'username':u[1],'email':u[2],'full_name':u[3],'role':u[4]}
    return None

def register_user(username, email, password, full_name):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute('INSERT INTO users (username,email,password,full_name,role) VALUES (?,?,?,?,?)',
                  (username, email, hash_password(password), full_name, "user"))
        conn.commit(); conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        return False, "Username already exists!" if "username" in str(e) else "Email already registered!"
    except Exception as e:
        return False, str(e)

def update_last_login(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute('UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?',(uid,))
    conn.commit(); conn.close()

def log_activity(uid, atype, desc):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute('INSERT INTO activity_logs (user_id,activity_type,description) VALUES (?,?,?)',(uid,atype,desc))
    conn.commit(); conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT id,username,email,full_name,role,created_at,last_login,is_active FROM users ORDER BY created_at DESC', conn)
    conn.close(); return df

def get_activity_logs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''SELECT al.id, u.username, al.activity_type, al.description, al.timestamp
        FROM activity_logs al JOIN users u ON al.user_id=u.id ORDER BY al.timestamp DESC LIMIT 100''', conn)
    conn.close(); return df

def update_user_status(uid, val):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute('UPDATE users SET is_active=? WHERE id=?',(val,uid)); conn.commit(); conn.close()

def delete_user(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=?',(uid,))
    c.execute('DELETE FROM activity_logs WHERE user_id=?',(uid,))
    conn.commit(); conn.close()

def change_user_role(uid, role):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute('UPDATE users SET role=? WHERE id=?',(role,uid)); conn.commit(); conn.close()


# ── MASTER CSS ──────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

    /* ═══ RESET & BASE ═══ */
    *, *::before, *::after { box-sizing: border-box; }
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0f0f1a !important;
    }

    /* ═══ APP BACKGROUND ═══ */
    .stApp {
        background: #f7f5ff !important;
        min-height: 100vh;
    }

    /* ═══ HIDE STREAMLIT CHROME ═══ */
    #MainMenu, footer, header { visibility: hidden !important; }
    .stDeployButton { display: none !important; }

    /* ═══ SIDEBAR ═══ */
    [data-testid="stSidebar"] {
        background: #0b0720 !important;
        border-right: 1px solid rgba(139,92,246,0.2) !important;
        box-shadow: 4px 0 24px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stSidebar"] > div { padding-top: 0 !important; }
    [data-testid="stSidebar"] * { color: #c4b5fd !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #fff !important; }
    [data-testid="stSidebar"] .stRadio > label { color: #a78bfa !important; font-weight: 600 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        color: #d8b4fe !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        padding: 0.55rem 0.75rem !important;
        border-radius: 10px !important;
        transition: background 0.2s !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
        background: rgba(139,92,246,0.15) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(139,92,246,0.2) !important;
    }

    /* Sidebar logout button */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(239,68,68,0.12) !important;
        border: 1px solid rgba(239,68,68,0.35) !important;
        color: #fca5a5 !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.2s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(239,68,68,0.25) !important;
        border-color: #ef4444 !important;
        color: #fff !important;
        transform: none !important;
        box-shadow: 0 0 12px rgba(239,68,68,0.3) !important;
    }

    /* ═══ MAIN CONTENT PADDING ═══ */
    .main .block-container {
        padding: 2rem 3rem !important;
        max-width: 1280px !important;
    }

    /* ═══ TYPOGRAPHY ═══ */
    h1 { color: #0f0f1a !important; font-weight: 800 !important; letter-spacing: -0.04em !important; font-size: 2.2rem !important; }
    h2 { color: #1e1b4b !important; font-weight: 700 !important; letter-spacing: -0.03em !important; }
    h3 { color: #1e1b4b !important; font-weight: 700 !important; }
    p  { color: #2d2a52 !important; line-height: 1.7 !important; }
    label { color: #1e1b4b !important; font-weight: 600 !important; }

    /* ═══ INPUTS ═══ */
    .stTextInput > div > div > input {
        background: #f9f7ff !important;
        border: 2px solid #e5e0ff !important;
        border-radius: 12px !important;
        color: #0f0f1a !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding: 0.7rem 1rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 4px rgba(124,58,237,0.12) !important;
        background: #fff !important;
    }
    .stTextInput > div > div > input::placeholder { color: #aca8cc !important; }
    .stTextInput label {
        color: #1e1b4b !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        margin-bottom: 0.4rem !important;
    }

    /* ═══ MAIN BUTTONS ═══ */
    .stButton > button {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        border-radius: 12px !important;
        padding: 0.65rem 1.4rem !important;
        border: none !important;
        cursor: pointer !important;
        transition: all 0.22s cubic-bezier(.4,0,.2,1) !important;
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(124,58,237,0.35) !important;
        letter-spacing: 0.01em !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(124,58,237,0.45) !important;
    }
    .stButton > button:active { transform: translateY(0px) !important; }

    /* ═══ METRICS ═══ */
    [data-testid="metric-container"],
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #ede9fe !important;
        border-radius: 16px !important;
        padding: 1.5rem 1.8rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(124,58,237,0.06) !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    [data-testid="metric-container"]:hover,
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 24px rgba(124,58,237,0.15) !important;
    }
    [data-testid="stMetricLabel"] > div {
        color: #7c3aed !important;
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }
    [data-testid="stMetricValue"] > div {
        color: #0f0f1a !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        letter-spacing: -0.03em !important;
    }

    /* ═══ TABS ═══ */
    .stTabs [data-baseweb="tab-list"] {
        background: #ede9fe !important;
        border-radius: 14px !important;
        padding: 5px !important;
        gap: 4px !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 100 !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 0 2px 12px rgba(124,58,237,0.08) !important;
        border: 1px solid rgba(124,58,237,0.1) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        color: #6d28d9 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1.2rem !important;
        transition: all 0.2s !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(124,58,237,0.1) !important; }
    .stTabs [aria-selected="true"] {
        background: #7c3aed !important;
        color: #ffffff !important;
        box-shadow: 0 2px 10px rgba(124,58,237,0.35) !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem !important; }

    /* ═══ EXPANDERS ═══ */
    [data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #ede9fe !important;
        border-radius: 14px !important;
        margin-bottom: 0.6rem !important;
        overflow: hidden !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
        transition: box-shadow 0.2s !important;
    }
    [data-testid="stExpander"]:hover { box-shadow: 0 4px 16px rgba(124,58,237,0.1) !important; }
    [data-testid="stExpander"] summary {
        background: #faf8ff !important;
        padding: 1rem 1.2rem !important;
        color: #1e1b4b !important;
        font-weight: 600 !important;
        font-size: 0.93rem !important;
        border-bottom: 1px solid #ede9fe !important;
    }
    [data-testid="stExpander"] summary:hover { background: #f3f0ff !important; }

    /* ═══ DATAFRAME ═══ */
    [data-testid="stDataFrame"] {
        border-radius: 14px !important;
        overflow: hidden !important;
        border: 1px solid #ede9fe !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }

    /* ═══ ALERTS ═══ */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border-left-width: 4px !important;
        font-weight: 500 !important;
    }
    [data-testid="stAlert"] p { color: inherit !important; }

    /* ═══ SELECT ═══ */
    .stSelectbox [data-baseweb="select"] > div {
        background: #f9f7ff !important;
        border: 2px solid #e5e0ff !important;
        border-radius: 12px !important;
        color: #0f0f1a !important;
        font-weight: 500 !important;
    }
    .stSelectbox label {
        color: #1e1b4b !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.07em !important;
        text-transform: uppercase !important;
    }

    /* ═══ TEXTAREA ═══ */
    .stTextArea textarea {
        background: #f9f7ff !important;
        border: 2px solid #e5e0ff !important;
        border-radius: 12px !important;
        color: #0f0f1a !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 0.88rem !important;
        line-height: 1.6 !important;
    }
    .stTextArea textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 4px rgba(124,58,237,0.12) !important;
    }
    .stTextArea label {
        color: #1e1b4b !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
    }

    /* ═══ DIVIDER ═══ */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #ddd6fe, transparent) !important;
        margin: 1.5rem 0 !important;
    }

    /* ═══ DOWNLOAD BUTTON ═══ */
    [data-testid="stDownloadButton"] button {
        background: #0f0f1a !important;
        color: #fff !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: #1e1b4b !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3) !important;
    }

    /* ═══ CUSTOM COMPONENTS ═══ */

    .page-hero {
        background: linear-gradient(135deg, #0b0720 0%, #1e1b4b 100%);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .page-hero::before {
        content: '';
        position: absolute;
        right: -40px; top: -40px;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(124,58,237,0.3), transparent 70%);
        border-radius: 50%;
    }
    .page-hero::after {
        content: '';
        position: absolute;
        left: 30%; bottom: -30px;
        width: 120px; height: 120px;
        background: radial-gradient(circle, rgba(79,70,229,0.2), transparent 70%);
        border-radius: 50%;
    }
    .page-hero h1 {
        color: #ffffff !important;
        font-size: 1.9rem !important;
        margin: 0 0 0.4rem !important;
        position: relative; z-index: 1;
    }
    .page-hero p {
        color: rgba(196,181,253,0.85) !important;
        font-size: 0.92rem !important;
        margin: 0 !important;
        position: relative; z-index: 1;
    }

    .icard {
        background: #fff;
        border: 1px solid #ede9fe;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }
    .icard:hover { box-shadow: 0 6px 20px rgba(124,58,237,0.10); }
    .icard-label {
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #7c3aed !important; margin-bottom: 0.5rem;
    }
    .icard-value { font-size: 1rem; font-weight: 600; color: #0f0f1a !important; }

    .frow {
        display: flex; gap: 0.9rem; align-items: flex-start;
        padding: 0.85rem 0; border-bottom: 1px solid #f3f0ff;
    }
    .frow:last-child { border-bottom: none; }
    .frow-icon {
        width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0;
        background: linear-gradient(135deg, #ede9fe, #ddd6fe);
        display: flex; align-items: center; justify-content: center; font-size: 1rem;
    }
    .frow-title { font-size: 0.9rem; font-weight: 700; color: #0f0f1a !important; margin-bottom: 0.15rem; }
    .frow-desc  { font-size: 0.82rem; color: #6b7280 !important; line-height: 1.5; }

    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
    }
    .badge-admin    { background: #fef2f2; color: #dc2626 !important; border: 1px solid #fecaca; }
    .badge-user     { background: #eff6ff; color: #2563eb !important; border: 1px solid #bfdbfe; }
    .badge-active   { background: #f0fdf4; color: #16a34a !important; border: 1px solid #bbf7d0; }
    .badge-inactive { background: #fef2f2; color: #dc2626 !important; border: 1px solid #fecaca; }

    .demo-box {
        background: linear-gradient(135deg, #f5f3ff, #ede9fe);
        border-radius: 12px; padding: 1rem 1.2rem;
        border: 1px solid #ddd6fe; margin-top: 1rem;
    }
    .demo-box .dlabel { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #7c3aed !important; margin-bottom: 0.5rem; }
    .demo-box .dcred  { font-family: 'Fira Code', monospace; font-size: 0.88rem; color: #1e1b4b !important; }
    .demo-box .dnote  { font-size: 0.78rem; color: #6b7280 !important; margin-top: 0.5rem; }

    .sb-profile {
        background: rgba(139,92,246,0.1);
        border: 1px solid rgba(139,92,246,0.2);
        border-radius: 16px; padding: 1.2rem;
        text-align: center; margin: 1rem 0;
    }
    .sb-avatar {
        width: 60px; height: 60px; border-radius: 50%;
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.6rem; margin: 0 auto 0.8rem;
        box-shadow: 0 4px 16px rgba(124,58,237,0.4);
    }
    .sb-name { font-weight: 700; font-size: 0.95rem; color: #fff !important; margin-bottom: 0.2rem; }
    .sb-role { font-size: 0.75rem; color: #a78bfa !important; }

    .sb-stat {
        background: rgba(139,92,246,0.08); border-radius: 10px;
        padding: 0.6rem 0.9rem;
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 0.5rem;
    }
    .sb-stat-label { font-size: 0.78rem; color: #a78bfa !important; }
    .sb-stat-val   { font-size: 0.88rem; font-weight: 700; color: #e9d5ff !important; }

    .sec-head {
        font-size: 0.75rem; font-weight: 800; color: #7c3aed !important;
        text-transform: uppercase; letter-spacing: 0.12em;
        padding-bottom: 0.6rem; border-bottom: 2px solid #ede9fe;
        margin-bottom: 1.2rem;
    }

    .about-hero {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border-radius: 20px; padding: 2rem; margin-bottom: 1rem;
        position: relative; overflow: hidden;
    }
    .about-hero::before {
        content: '🔐'; position: absolute; right: 1.5rem; bottom: 1rem;
        font-size: 6rem; opacity: 0.1; line-height: 1;
    }
    .about-hero h2 { color: #fff !important; margin: 0 0 0.6rem !important; font-size: 1.4rem !important; }
    .about-hero p  { color: rgba(196,181,253,0.9) !important; font-size: 0.9rem !important; margin: 0 !important; max-width: 480px; line-height: 1.75; }

    /* Auth layout */
    .auth-wrap {
        background: linear-gradient(145deg, #0b0720 0%, #130f30 50%, #0b1640 100%);
        padding: 3rem 1rem 4rem;
        margin: -6rem -3rem -3rem;
    }
    .auth-logo-box { text-align: center; margin-bottom: 2rem; }
    .auth-icon-ring {
        width: 68px; height: 68px;
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        border-radius: 20px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 2rem; margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(124,58,237,0.45);
    }
    .auth-app-name {
        font-size: 2rem; font-weight: 800; letter-spacing: -0.04em;
        color: #ffffff !important; margin: 0;
    }
    .auth-app-sub {
        font-size: 0.85rem; color: rgba(255,255,255,0.45) !important; margin: 0.3rem 0 0;
    }
    .auth-card-box {
        background: #ffffff;
        border-radius: 24px;
        padding: 2.5rem 2.2rem;
        box-shadow: 0 32px 80px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,1);
    }
    .auth-card-title { font-size: 1.3rem; font-weight: 800; color: #0f0f1a !important; margin-bottom: 0.25rem; }
    .auth-card-sub2  { font-size: 0.83rem; color: #6b7280 !important; margin-bottom: 1.6rem; }
    </style>
    """, unsafe_allow_html=True)


# ── AUTH PAGES ──────────────────────────────────────────────────────────────────
def login_page():
    inject_css()
    st.markdown("<div class='auth-wrap'>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
        <div class='auth-logo-box'>
            <div class='auth-icon-ring'>🔐</div>
            <div class='auth-app-name'>SecureAuth</div>
            <div class='auth-app-sub'>Enterprise access management</div>
        </div>
        <div class='auth-card-box'>
        <div class='auth-card-title'>Welcome back</div>
        <div class='auth-card-sub2'>Sign in to continue to your dashboard</div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="your_username", key="li_u")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="li_p")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sign In →", use_container_width=True, key="signin"):
                if username and password:
                    user = verify_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        update_last_login(user['id'])
                        log_activity(user['id'], 'login', f"User {username} logged in")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
                else:
                    st.warning("Please enter both username and password.")
        with c2:
            if st.button("Create Account", use_container_width=True, key="goto_reg"):
                st.session_state.page = 'register'
                st.rerun()

        st.markdown("""
        <div class='demo-box'>
            <div class='dlabel'>Demo Credentials</div>
            <div class='dcred'>Username: <strong>admin</strong> &nbsp;·&nbsp; Password: <strong>admin123</strong></div>
            <div class='dnote'>💡 Or register your own account using the button above</div>
        </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def register_page():
    inject_css()
    st.markdown("<div class='auth-wrap'>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
        <div class='auth-logo-box'>
            <div class='auth-icon-ring'>✨</div>
            <div class='auth-app-name'>Create Account</div>
            <div class='auth-app-sub'>Join SecureAuth in seconds</div>
        </div>
        <div class='auth-card-box'>
        <div class='auth-card-title'>New account</div>
        <div class='auth-card-sub2'>Fill in your details to get started</div>
        """, unsafe_allow_html=True)

        full_name = st.text_input("Full Name", placeholder="Jane Doe", key="rn")
        username  = st.text_input("Username",  placeholder="janedoe", key="ru")
        email     = st.text_input("Email",     placeholder="jane@example.com", key="re")
        password  = st.text_input("Password",  type="password", placeholder="Min. 6 characters", key="rp")
        confirm   = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="rc")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Register →", use_container_width=True, key="register"):
                if not all([full_name, username, email, password, confirm]):
                    st.warning("Please fill in all fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    ok, msg = register_user(username, email, password, full_name)
                    if ok:
                        st.success(f"🎉 {msg}")
                        st.balloons()
                    else:
                        st.error(msg)
        with c2:
            if st.button("← Back to Login", use_container_width=True, key="back"):
                st.session_state.page = 'login'
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── DASHBOARD ───────────────────────────────────────────────────────────────────
def user_dashboard():
    u = st.session_state.user
    first = u['full_name'].split()[0]

    st.markdown(f"""
    <div class='page-hero'>
        <h1>Good day, {first} 👋</h1>
        <p>Here's everything about your account at a glance.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("👤 Username", u['username'])
    with col2: st.metric("📧 Email", u['email'])
    with col3: st.metric("🎭 Role", u['role'].upper())

    st.divider()

    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute('SELECT created_at, last_login FROM users WHERE id=?', (u['id'],))
    info = c.fetchone(); conn.close()

    st.markdown("<div class='sec-head'>Account Details</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='icard'>
            <div class='icard-label'>📅 Account Created</div>
            <div class='icard-value'>{info[0]}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        last = info[1] if info[1] else "First login ever"
        st.markdown(f"""
        <div class='icard'>
            <div class='icard-label'>🕐 Last Login</div>
            <div class='icard-value'>{last}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown("<div class='sec-head'>Recent Activity</div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_PATH)
    act = pd.read_sql_query(
        'SELECT activity_type AS "Type", description AS "Description", timestamp AS "Timestamp" FROM activity_logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 10',
        conn, params=(u['id'],))
    conn.close()
    if not act.empty:
        st.dataframe(act, use_container_width=True)
    else:
        st.info("No activity recorded yet.")

    st.divider()

    st.markdown("<div class='sec-head'>About SecureAuth</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='about-hero'>
        <h2>What is SecureAuth?</h2>
        <p>
        A full-featured, self-hosted authentication and user management platform.
        SHA-256 hashed passwords, role-based access control, full activity auditing —
        all on a lightweight SQLite backend with zero external dependencies.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class='icard'>
            <div class='icard-label' style='margin-bottom:1rem;'>⚡ Core Features</div>
            <div class='frow'>
                <div class='frow-icon'>🛡️</div>
                <div><div class='frow-title'>SHA-256 Password Hashing</div><div class='frow-desc'>Passwords are never stored in plain text — always hashed before storage.</div></div>
            </div>
            <div class='frow'>
                <div class='frow-icon'>👥</div>
                <div><div class='frow-title'>Role-Based Access Control</div><div class='frow-desc'>Admin and User tiers with distinct permissions and panel access.</div></div>
            </div>
            <div class='frow'>
                <div class='frow-icon'>📊</div>
                <div><div class='frow-title'>Full Activity Audit Log</div><div class='frow-desc'>Every login, logout, and admin action is timestamped and stored.</div></div>
            </div>
            <div class='frow'>
                <div class='frow-icon'>⚙️</div>
                <div><div class='frow-title'>Admin Control Panel</div><div class='frow-desc'>Promote, deactivate, delete users and run live SQL queries.</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='icard'>
            <div class='icard-label' style='margin-bottom:1rem;'>🛠️ Technology Stack</div>
            <div class='frow'>
                <div class='frow-icon'>🐍</div>
                <div><div class='frow-title'>Python 3</div><div class='frow-desc'>Clean, readable backend with no unnecessary boilerplate.</div></div>
            </div>
            <div class='frow'>
                <div class='frow-icon'>🌊</div>
                <div><div class='frow-title'>Streamlit</div><div class='frow-desc'>Reactive UI framework — real-time updates, no JavaScript required.</div></div>
            </div>
            <div class='frow'>
                <div class='frow-icon'>🗄️</div>
                <div><div class='frow-title'>SQLite</div><div class='frow-desc'>Serverless relational database — file-based, zero configuration.</div></div>
            </div>
            <div class='frow'>
                <div class='frow-icon'>🔒</div>
                <div><div class='frow-title'>hashlib (SHA-256)</div><div class='frow-desc'>Industry-standard one-way hashing for all stored credentials.</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── ADMIN PANEL ─────────────────────────────────────────────────────────────────
def admin_panel():
    st.markdown("""
    <div class='page-hero'>
        <h1>⚙️ Admin Control Panel</h1>
        <p>Manage users, review audit logs, and run database queries.</p>
    </div>
    """, unsafe_allow_html=True)

    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_active=1"); active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM activity_logs"); logs = c.fetchone()[0]
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("👥 Total Users", total)
    with col2: st.metric("🟢 Active", active)
    with col3: st.metric("🔴 Inactive", total - active)
    with col4: st.metric("📋 Log Entries", logs)

    st.divider()

    tab1, tab2, tab3 = st.tabs(["  👥  User Management  ", "  📝  Activity Logs  ", "  🗄️  SQL Query Tool  "])

    with tab1:
        st.markdown("<div class='sec-head'>Registered Users</div>", unsafe_allow_html=True)
        users_df = get_all_users()
        for _, row in users_df.iterrows():
            s_icon  = "🟢" if row['is_active'] else "🔴"
            r_label = "👑 Admin" if row['role'] == 'admin' else "👤 User"
            with st.expander(f"{s_icon}  {row['username']}  ·  {row['email']}  ·  {r_label}"):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                with col1:
                    st.markdown(f"""
                    <div class='icard-label'>Full Name</div>
                    <div class='icard-value' style='margin-bottom:0.8rem;'>{row['full_name']}</div>
                    <div class='icard-label'>Status</div>
                    <span class='badge {"badge-active" if row["is_active"] else "badge-inactive"}'>
                        {"Active" if row["is_active"] else "Inactive"}
                    </span>
                    """, unsafe_allow_html=True)
                with col2:
                    last = row['last_login'] if row['last_login'] else 'Never'
                    st.markdown(f"""
                    <div class='icard-label'>Created</div>
                    <div class='icard-value' style='font-size:0.85rem;margin-bottom:0.8rem;'>{row['created_at']}</div>
                    <div class='icard-label'>Last Login</div>
                    <div class='icard-value' style='font-size:0.85rem;'>{last}</div>
                    """, unsafe_allow_html=True)
                with col3:
                    new_role = st.selectbox("Change Role", ["user", "admin"],
                                            index=0 if row['role'] == 'user' else 1,
                                            key=f"role_{row['id']}")
                    if st.button("Update Role", key=f"upd_{row['id']}"):
                        change_user_role(row['id'], new_role)
                        st.success(f"Role updated to {new_role}")
                        st.rerun()
                with col4:
                    if row['username'] != 'admin':
                        if row['is_active']:
                            if st.button("Deactivate", key=f"deact_{row['id']}"):
                                update_user_status(row['id'], 0)
                                log_activity(st.session_state.user['id'], 'admin', f"Deactivated {row['username']}")
                                st.rerun()
                        else:
                            if st.button("Activate", key=f"act_{row['id']}"):
                                update_user_status(row['id'], 1)
                                log_activity(st.session_state.user['id'], 'admin', f"Activated {row['username']}")
                                st.rerun()
                        if st.button("🗑 Delete", key=f"del_{row['id']}"):
                            delete_user(row['id'])
                            log_activity(st.session_state.user['id'], 'admin', f"Deleted {row['username']}")
                            st.rerun()
                    else:
                        st.markdown("<span class='badge badge-admin'>🔒 Protected</span>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='sec-head'>Audit Log — Last 100 Events</div>", unsafe_allow_html=True)
        logs_df = get_activity_logs()
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True, height=420)
            st.download_button("📥 Export as CSV", logs_df.to_csv(index=False),
                               f"audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
        else:
            st.info("No logs found.")

    with tab3:
        st.markdown("<div class='sec-head'>Live SQL Query</div>", unsafe_allow_html=True)
        st.warning("⚠️ Use SELECT queries only. Write operations may corrupt application state.")
        query = st.text_area("SQL Statement", value="SELECT * FROM users LIMIT 10;", height=130)
        if st.button("▶  Run Query"):
            try:
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql_query(query, conn); conn.close()
                st.success(f"✅ {len(df)} row(s) returned.")
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Export as CSV", df.to_csv(index=False),
                                   f"query_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
            except Exception as e:
                st.error(f"Query failed: {e}")


# ── MAIN ────────────────────────────────────────────────────────────────────────
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user'      not in st.session_state: st.session_state.user      = None
if 'page'      not in st.session_state: st.session_state.page      = 'login'

def main():
    init_db()
    inject_css()

    if not st.session_state.logged_in:
        login_page() if st.session_state.page == 'login' else register_page()
        return

    u = st.session_state.user

    with st.sidebar:
        st.markdown(f"""
        <div class='sb-profile'>
            <div class='sb-avatar'>{'👑' if u['role']=='admin' else '👤'}</div>
            <div class='sb-name'>{u['full_name']}</div>
            <div class='sb-role'>@{u['username']} · {u['role'].upper()}</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if u['role'] == 'admin':
            page = st.radio("nav", ["🏠  Dashboard", "⚙️  Admin Panel"],
                            key="nav", label_visibility="collapsed")
        else:
            page = "🏠  Dashboard"
            st.markdown("<p style='color:#a78bfa!important;font-size:0.9rem;padding:0.3rem 0.5rem;font-weight:600;'>🏠 Dashboard</p>", unsafe_allow_html=True)

        st.divider()

        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM activity_logs WHERE user_id=?", (u['id'],))
        n_logs = c.fetchone()[0]; conn.close()

        st.markdown(f"""
        <div class='sb-stat'>
            <span class='sb-stat-label'>📋 Log entries</span>
            <span class='sb-stat-val'>{n_logs}</span>
        </div>
        <div class='sb-stat'>
            <span class='sb-stat-label'>🎭 Role</span>
            <span class='sb-stat-val'>{u['role'].title()}</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        if st.button("🚪  Sign Out", use_container_width=True):
            log_activity(u['id'], 'logout', f"User {u['username']} logged out")
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()

    if "Dashboard" in page:
        user_dashboard()
    elif "Admin" in page and u['role'] == 'admin':
        admin_panel()

if __name__ == "__main__":
    main()
