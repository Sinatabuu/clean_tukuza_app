
import sqlite3
import os
import streamlit as st

@st.cache_resource
def get_db_connection():
    if os.environ.get("STREAMLIT_SERVER_ENVIRONMENT") == "cloud":
        db_file = "/tmp/discipleship_agent.db"
    else:
        db_file = os.path.join(os.path.dirname(__file__), "discipleship_agent.db")

    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        st.error(f"❌ Failed to connect to database at {db_file}: {e}")
        st.stop()

def get_schema_version(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 0

def set_schema_version(cursor, version):
    cursor.execute("DELETE FROM schema_version")
    cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))

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

def run_schema_upgrades():
    conn = get_db_connection()
    cursor = conn.cursor()
    current_version = get_schema_version(cursor)

    if current_version < 1:
        create_user_profiles_table(cursor)
        create_gift_assessments_table(cursor)
        create_growth_journal_table(cursor)
        set_schema_version(cursor, 1)
        conn.commit()
        st.info("✅ Initialized database schema to version 1.")

    if current_version < 2:
        try:
            cursor.execute("ALTER TABLE growth_journal ADD COLUMN sentiment TEXT")
            conn.commit()
            st.success("🔁 Upgraded DB schema to version 2 (added 'sentiment' column).")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                st.warning("⚠️ 'sentiment' column already exists. Skipping.")
            else:
                st.error(f"DB upgrade error: {e}")
        set_schema_version(cursor, 2)

    conn.close()
