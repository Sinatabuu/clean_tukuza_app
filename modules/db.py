import psycopg2
import streamlit as st

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["DB"]["DB_HOST"],
            port=st.secrets["DB"]["DB_PORT"],
            database=st.secrets["DB"]["DB_NAME"],
            user=st.secrets["DB"]["DB_USER"],
            password=st.secrets["DB"]["DB_PASSWORD"]
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

def run_schema_upgrades():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    entry_text TEXT NOT NULL,
                    reflection_text TEXT,
                    faith_goal TEXT,
                    mood VARCHAR(50),
                    sentiment FLOAT
                );
            """)
            conn.commit()
    except psycopg2.Error as e:
        st.error(f"Schema upgrade failed: {e}")
    finally:
        conn.close()

def insert_journal_entry(user_id, entry_text, reflection_text, faith_goal, mood, sentiment):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO journal_entries (user_id, entry_text, reflection_text, faith_goal, mood, sentiment)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (user_id, entry_text, reflection_text, faith_goal, mood, sentiment))
            entry_id = cur.fetchone()[0]
            conn.commit()
            return entry_id
    except psycopg2.Error as e:
        st.error(f"Failed to insert journal entry: {e}")
        return None
    finally:
        conn.close()

def fetch_journal_entries(user_id):
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, entry_date, entry_text, reflection_text, faith_goal, mood, sentiment
                FROM journal_entries
                WHERE user_id = %s
                ORDER BY entry_date DESC;
            """, (user_id,))
            entries = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "entry_date": row[1],
                    "entry_text": row[2],
                    "reflection_text": row[3],
                    "faith_goal": row[4],
                    "mood": row[5],
                    "sentiment": row[6]
                } for row in entries
            ]
    except psycopg2.Error as e:
        st.error(f"Failed to fetch journal entries: {e}")
        return []
    finally:
        conn.close()

def delete_journal_entry(entry_id):
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM journal_entries WHERE id = %s;", (entry_id,))
            conn.commit()
            return cur.rowcount > 0
    except psycopg2.Error as e:
        st.error(f"Failed to delete journal entry: {e}")
        return False
    finally:
        conn.close()