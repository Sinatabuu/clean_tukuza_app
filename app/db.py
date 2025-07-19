import os
import sqlite3
import streamlit as st

# ---------------------------
# 🔌 Database Connection
# ---------------------------
@st.cache_resource
def get_db_connection():
    if os.environ.get("STREAMLIT_SERVER_ENVIRONMENT") == "cloud":
        db_file = "/tmp/discipleship_agent.db"
    else:
        db_file = os.path.join(os.path.dirname(__file__), "../discipleship_agent.db")

    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        st.error(f"❌ DB connection failed: {e}")
        st.stop()

# ---------------------------
# 📊 Schema Versioning
# ---------------------------
def get_schema_version(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 0

def set_schema_version(cursor, version):
    cursor.execute("DELETE FROM schema_version")
    cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))

# ---------------------------
# 🔧 Table Creators
# ---------------------------
def create_user_profiles_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            stage TEXT NOT NULL
        )
    """)

def create_gift_assessments_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gift_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            primary_gift TEXT,
            secondary_gift TEXT,
            primary_role TEXT,
            secondary_role TEXT,
            ministries TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles(id)
        )
    """)

def create_growth_journal_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS growth_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry TEXT,
            reflection TEXT,
            goal TEXT,
            mood TEXT,
            sentiment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles(id)
        )
    """)

# ---------------------------
# ⬆️ Schema Upgrader
# ---------------------------
def run_schema_upgrades():
    conn = get_db_connection()
    cursor = conn.cursor()
    current_version = get_schema_version(cursor)

    st.write(f"🔍 Current DB schema version: {current_version}")  # Debugging line

    if current_version < 1:
        st.write("🧱 Creating tables...")
        create_user_profiles_table(cursor)
        create_gift_assessments_table(cursor)
        create_growth_journal_table(cursor)
        set_schema_version(cursor, 1)
        conn.commit()

    if current_version < 2:
        try:
            cursor.execute("ALTER TABLE growth_journal ADD COLUMN sentiment TEXT")
            set_schema_version(cursor, 2)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                st.error(f"Schema upgrade to v2 failed: {e}")

    conn.close()
