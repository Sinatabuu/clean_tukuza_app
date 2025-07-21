import streamlit as st
import os
import sys

# Standard libraries that are truly global for app.py's direct use
import sqlite3 # Used in Login/Signup
import pandas as pd # Used if you display dataframes directly in app.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 1. Appending module path ---
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. Custom modules ---
from modules.biblebot_ui import biblebot_ui
from modules.db import (
    get_db_connection,
    insert_gift_assessment,
    fetch_latest_gift_assessment,
    delete_gift_assessment_for_user,
    insert_journal_entry,
    fetch_journal_entries
)

# --- 3. Hugging Face Model Loaders (Enhanced with @st.cache_resource) ---
# These are global to app.py and potentially passed to modules
from transformers import pipeline

@st.cache_resource
def load_classifier_model():
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

@st.cache_resource
def load_sentiment_model():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Load models once at app startup
classifier = load_classifier_model()
sentiment_analyzer = load_sentiment_model()


# --- 4. Database Initialization and Schema Upgrade ---
run_schema_upgrades()


# --- 5. Translation Functions (Moved to a common utility file if many modules use them) ---
# For now, keep them here if only app.py and perhaps one module uses them
from langdetect import detect
from deep_translator import GoogleTranslator

def translate_user_input(text, target_lang="en"):
    try:
        detected_lang = detect(text)
        if detected_lang != 'en':
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            return translated, detected_lang
        return text, detected_lang
    except Exception: # Catch any error during detection/translation
        return text, "en" # Fallback to original text and English

def translate_bot_response(text, target_lang):
    if target_lang != 'en':
        try:
            return GoogleTranslator(source='en', target=target_lang).translate(text)
        except Exception: # Catch any error during translation
            return text # Return original if translation fails
    return text

# --- 6. App Configuration ---
st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="wide")

# --- 7. Main Streamlit Application Function ---
def main_app():
    """
    Main function for the Tukuza Yesu AI Toolkit Streamlit application.
    Handles user login, navigation, and dispatches to different tools.
    """
    # --- Session State Initialization ---
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'page' not in st.session_state:
        st.session_state.page = "Login"


    st.sidebar.title("✝️ Tukuza Yesu Toolkit 🚀")

    # --- Login/User Management Section (Main Entry Point) ---
    if st.session_state.page == "Login":
        st.header("Welcome to Tukuza!")
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

        with login_tab:
            st.markdown("### Existing User Login")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM user_profiles ORDER BY name")
            existing_users = cursor.fetchall()

            users = {row["name"]: row["id"] for row in existing_users}
            user_names = ["Select User"] + sorted(list(users.keys()))

            selected_user_name = st.selectbox("Select your profile", user_names, key="login_user_select")

            if selected_user_name != "Select User":
                st.session_state.user_id = users[selected_user_name]
                st.session_state.user_name = selected_user_name
                st.success(f"Logged in as {selected_user_name}!")
                st.session_state.page = "Dashboard"
                st.experimental_rerun()
            else:
                st.info("Or create a new profile in the 'Sign Up' tab.")

        with signup_tab:
            st.markdown("### Create New Profile")
            new_user_name = st.text_input("New User Name", key="new_user_name_input")
            new_user_email = st.text_input("Email (Optional)", key="new_user_email_input")
            selected_stage = st.selectbox("Select Discipleship Stage", ["Seeker", "Believer", "Disciple", "Leader"], key="new_user_stage_select")

            if st.button("Create Profile", key="create_profile_button"):
                if new_user_name:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO user_profiles (name, email, stage) VALUES (?, ?, ?)",
                                       (new_user_name, new_user_email, selected_stage))
                        conn.commit()
                        st.success(f"Profile '{new_user_name}' created successfully!")
                        st.session_state.user_id = cursor.lastrowid
                        st.session_state.user_name = new_user_name
                        st.session_state.page = "Dashboard"
                        st.experimental_rerun()
                    except sqlite3.IntegrityError:
                        st.error("A user with this name already exists. Please choose a different name.")
                else:
                    st.warning("Please enter a user name.")

    # --- Dashboard and Tool Selection ---
    elif st.session_state.page == "Dashboard":
        st.sidebar.write(f"Logged in as: **{st.session_state.user_name}**")
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.page = "Login"
            st.experimental_rerun()

        st.sidebar.subheader("Navigation")
        tool = st.sidebar.selectbox("🛠️ Select a Tool", [
            "🏠 Dashboard",
            "📖 BibleBot",
            "📘 Spiritual Growth Tracker",
            "🔖 Verse Classifier",
            "🌅 Daily Verse",
            "🧪 Spiritual Gifts Assessment"
        ], index=0, key="tool_selector_dashboard")

        # Handle tool selection
        if tool == "🏠 Dashboard":
            st.title(f"Dashboard for {st.session_state.user_name}")
            st.write("Welcome to your personalized discipleship dashboard.")
            st.info("Select a tool from the sidebar to begin.")

        elif tool == "📖 BibleBot":
            biblebot_ui()

        elif tool == "📘 Spiritual Growth Tracker":
            growth_tracker_ui(sentiment_analyzer) # Pass sentiment_analyzer

        elif tool == "🔖 Verse Classifier":
            st.subheader("Classify a Bible Verse")
            st.write("🧠 Using a Hugging Face model for classification.")
            candidate_labels = ["faith", "love", "hope", "salvation", "guidance", "suffering", "peace", "justice", "community", "forgiveness"]
            st.write(f"Considered Topics: {', '.join(candidate_labels)}")

            verse = st.text_area("Paste a Bible verse here:", key="verse_classifier_input")
            if st.button("Classify", key="classify_button"):
                if verse.strip() == "":
                    st.warning("Please enter a verse.")
                else:
                    result = classifier(verse, candidate_labels=candidate_labels, multi_label=False)
                    predicted_topic = result['labels'][0]
                    score = result['scores'][0]
                    st.success(f"🧠 Predicted Topic: **{predicted_topic}** (Confidence: {score:.2f})")
                    st.info(f"Top 3 predictions: {result['labels'][0]} ({result['scores'][0]:.2f}), {result['labels'][1]} ({result['scores'][1]:.2f}), {result['labels'][2]} ({result['scores'][2]:.2f})")

        elif tool == "🌅 Daily Verse":
            st.subheader("🌞 Your Daily Verse")
            verse_of_the_day = "“This is the day that the Lord has made; let us rejoice and be glad in it.” – Psalm 118:24"
            st.success(verse_of_the_day)

        elif tool == "🧪 Spiritual Gifts Assessment":
            gift_assessment_ui() # Call without arguments, as sentiment_analyzer is not used there
                                 # and joblib.load is handled internally.

# --- 8. Entry Point for the App ---
if __name__ == "__main__":
    main_app()

# --- 9. Credit (Always show) ---
st.markdown("---")
st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")