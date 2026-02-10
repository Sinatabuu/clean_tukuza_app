import json
import psycopg2
import streamlit as st

def get_db_connection():
    conn = psycopg2.connect(
        host=st.secrets["DB"]["DB_HOST"],
        port=st.secrets["DB"]["DB_PORT"],
        dbname=st.secrets["DB"]["DB_NAME"],
        user=st.secrets["DB"]["DB_USER"],
        password=st.secrets["DB"]["DB_PASSWORD"],
        sslmode="require",
    )
    return conn

def run_schema_upgrades():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
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

# ---------- Gift Assessment ----------
def insert_gift_assessment(session_id, language=None, answers=None, results=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO gift_assessments (session_id, language, answers_json, results_json)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (
                session_id,
                language,
                json.dumps(answers or {}, ensure_ascii=False),
                json.dumps(results or {}, ensure_ascii=False),
            ))
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    finally:
        conn.close()

def fetch_latest_gift_assessment(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, created_at, session_id, language, answers_json, results_json
                FROM gift_assessments
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
            """, (session_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "created_at": row[1],
                "session_id": row[2],
                "language": row[3],
                "answers": json.loads(row[4] or "{}"),
                "results": json.loads(row[5] or "{}"),
            }
    finally:
        conn.close()

# ---------- Journal ----------
def insert_journal_entry(user_id, entry_text, reflection_text=None, faith_goal=None, mood=None, sentiment=None):
    conn = get_db_connection()
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
    finally:
        conn.close()

def fetch_journal_entries(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, entry_date, entry_text, reflection_text, faith_goal, mood, sentiment
                FROM journal_entries
                WHERE user_id = %s
                ORDER BY entry_date DESC;
            """, (user_id,))
            rows = cur.fetchall()
            return [{
                "id": r[0],
                "entry_date": r[1],
                "entry_text": r[2],
                "reflection_text": r[3],
                "faith_goal": r[4],
                "mood": r[5],
                "sentiment": r[6],
            } for r in rows]
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
def delete_gift_assessment_for_user(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM gift_assessments WHERE session_id=%s;", (session_id,))
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()
