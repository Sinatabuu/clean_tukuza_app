import json
import streamlit as st
import psycopg2
import psycopg2.extras
import json



def get_db_connection():
    return psycopg2.connect(
        host=st.secrets["DB"]["DB_HOST"],
        port=st.secrets["DB"]["DB_PORT"],
        dbname=st.secrets["DB"]["DB_NAME"],
        user=st.secrets["DB"]["DB_USER"],
        password=st.secrets["DB"]["DB_PASSWORD"],
        sslmode="require",
    )


def run_schema_upgrades():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # ---- User profiles (needed for your Login UI) ----
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    email TEXT,
                    stage TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ---- Journal ----
            cur.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    entry_text TEXT NOT NULL,
                    reflection_text TEXT,
                    faith_goal TEXT,
                    mood VARCHAR(50),
                    sentiment FLOAT
                );
            """)

            # ---- Gift assessments ----
            cur.execute("""
                CREATE TABLE IF NOT EXISTS gift_assessments (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT NOT NULL,
                    language VARCHAR(20),
                    answers_json TEXT,
                    results_json TEXT
                );
            """)

            conn.commit()
    finally:
        conn.close()


# ---------- User Profiles ----------
def list_user_profiles():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM user_profiles ORDER BY name;")
            return cur.fetchall()  # list[dict]
    finally:
        conn.close()


def create_user_profile(name: str, email: str | None, stage: str):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO user_profiles (name, email, stage)
                VALUES (%s, %s, %s)
                RETURNING id, name;
                """,
                (name, email, stage),
            )
            row = cur.fetchone()
            conn.commit()
            return row  # {"id":..., "name":...}
    finally:
        conn.close()


#raise RuntimeError("DEBUG: db.py insert_gift_assessment UPDATED")

def insert_gift_assessment(session_id, language=None, answers=None, results=None):
    # Defensive: if someone accidentally passed a dict as 2nd arg
    if isinstance(language, dict) and results is None:
        results = language
        language = "en"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gift_assessments (session_id, language, answers_json, results_json)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    str(session_id),
                    str(language or "en"),
                    Json(answers or {}),   # <-- dict safe
                    Json(results or {}),   # <-- dict safe
                ),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    finally:
        conn.close()



def fetch_latest_gift_assessment(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, created_at, session_id, language, answers_json, results_json
                FROM gift_assessments
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (session_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "created_at": row["created_at"],
                "session_id": row["session_id"],
                "language": row["language"],
                "answers": json.loads(row["answers_json"] or "{}"),
                "results": json.loads(row["results_json"] or "{}"),
            }
    finally:
        conn.close()


def delete_gift_assessment_for_user(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM gift_assessments WHERE session_id=%s;", (session_id,))
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


# ---------- Journal ----------
def insert_journal_entry(user_id, entry_text, reflection_text=None, faith_goal=None, mood=None, sentiment=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO journal_entries (user_id, entry_text, reflection_text, faith_goal, mood, sentiment)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, entry_text, reflection_text, faith_goal, mood, sentiment),
            )
            entry_id = cur.fetchone()[0]
            conn.commit()
            return entry_id
    finally:
        conn.close()


def fetch_journal_entries(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, entry_date, entry_text, reflection_text, faith_goal, mood, sentiment
                FROM journal_entries
                WHERE user_id = %s
                ORDER BY entry_date DESC;
                """,
                (user_id,),
            )
            return cur.fetchall()  # list[dict]
    finally:
        conn.close()


def delete_journal_entry(entry_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM journal_entries WHERE id = %s;", (entry_id,))
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()
