import streamlit as st
from datetime import datetime
# Import the specific functions from db.py
from modules.db import insert_journal_entry, fetch_journal_entries, delete_journal_entry, get_db_connection, run_schema_upgrades
from transformers import pipeline


# Load sentiment model once
@st.cache_resource
def load_sentiment_model():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

sentiment_analyzer = load_sentiment_model()

def growth_tracker_ui():
    st.subheader("🧘‍♂️ Spiritual Growth Tracker")
    st.markdown("Use this space to reflect, journal your walk, and track your spiritual growth over time.")

    # Ensure user is authenticated first
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
        return # Important: return early if no user logged in

    # No need to get conn/cursor here directly, as helper functions handle it

    with st.form("journal_form", clear_on_submit=True):
        entry = st.text_area("📖 What’s on your heart today?", height=150)
        reflection = st.text_area("🔍 Reflection (optional)")
        goal = st.text_input("🎯 Faith Goal for the Week")
        mood = st.selectbox("🙂 How do you feel today?", ["Joyful", "Hopeful", "Anxious", "Grateful", "Tired", "Determined", "Other"])

        submitted = st.form_submit_button("💾 Save Entry")

        if submitted:
            if entry.strip():
                try:
                    sentiment = sentiment_analyzer(entry)[0]['label']
                    # Call the helper function from db.py
                    insert_journal_entry(st.session_state.user_id, entry, reflection, goal, mood, sentiment)
                    st.success("📝 Journal entry saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving entry: {e}")
            else:
                st.warning("Entry cannot be empty.")

    st.markdown("---")
    st.markdown("### 📚 Your Past Journal Entries")
    # Call the helper function from db.py
    journal_entries = fetch_journal_entries(st.session_state.user_id)

    if not journal_entries:
        st.info("No journal entries found. Start writing today!")
    else:
        # Ensure that the order of unpacking matches the SELECT query in fetch_journal_entries
        # SELECT entry_text, reflection_text, faith_goal, mood, timestamp, sentiment, id
        for i, (entry, reflection, goal, mood, timestamp, sentiment, entry_id) in enumerate(journal_entries, 1):
            with st.expander(f"{i}. {timestamp.strftime('%Y-%m-%d %H:%M')} | Mood: {mood} | Sentiment: {sentiment}"): # Format timestamp
                st.markdown(f"**Entry:** {entry}")
                if reflection:
                    st.markdown(f"**Reflection:** {reflection}")
                if goal:
                    st.markdown(f"**Goal:** {goal}")
                # Delete button
                if st.button("🗑 Delete", key=f"delete_{entry_id}"):
                    try:
                        delete_journal_entry(entry_id) # Call the helper function from db.py
                        st.success("Entry deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting entry: {e}")


    # Optional Summary Analytics
    st.markdown("---")
    st.markdown("### 📈 Entry Summary")
    entry_count = len(journal_entries)
    sentiment_counts = {}
    for _, _, _, _, _, sentiment, _ in journal_entries: # Unpack to get sentiment
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    st.markdown(f"**Total Entries:** {entry_count}")
    for sentiment, count in sentiment_counts.items():
        st.markdown(f"- {sentiment}: {count}")