from transformers import pipeline
import streamlit as st
import sqlite3
import os

# ---------------------------
# 🤗 Hugging Face Pipelines
# ---------------------------

@st.cache_resource
def load_classifier_model():
    """
    Loads a zero-shot classification model from Hugging Face.
    """
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

@st.cache_resource
def load_sentiment_model():
    """
    Loads a sentiment analysis model from Hugging Face.
    """
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Initialize once for global use
classifier = load_classifier_model()
sentiment_analyzer = load_sentiment_model()

# ---------------------------
# 📦 SQLite Utilities (moved from app.py to here)
# ---------------------------

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

# ---------------------------
# 📘 Growth Journal Functions
# ---------------------------
#---------import sqlite3
from db import get_db_connection

def insert_journal_entry(user_id, entry, reflection, goal, mood, sentiment):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO growth_journal (user_id, entry, reflection, goal, mood, sentiment)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, entry, reflection, goal, mood, sentiment))
    conn.commit()
    conn.close()

def fetch_journal_entries(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM growth_journal
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (user_id,))
    entries = cursor.fetchall()
    conn.close()
    return entries

def delete_journal_entry(entry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM growth_journal WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
