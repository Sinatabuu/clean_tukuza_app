import streamlit as st
import os
import joblib
import numpy as np
import pandas as pd
import sqlite3
import sys
import json
from openai import OpenAI # Assuming you use this for something not shown here
from langdetect import detect
from deep_translator import GoogleTranslator
from transformers import pipeline # For the verse classifier and sentiment analysis

# --- 1. Appending module path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. Custom modules ---
# Ensure these files and functions exist in their respective paths
from modules.biblebot_ui import biblebot_ui
# Assuming you'll uncomment these and they contain the UI functions
from modules.gift_assessment import gift_assessment_ui , sentiment_analyzer # Assuming this is used in gift_assessment_ui
from modules.growth_tracker_ui import growth_tracker_ui # Assuming this module exists

# Assuming these are in db.py and correctly handle their logic
from db import get_db_connection, run_schema_upgrades

# --- 3. Initialize OpenAI Client (if used) ---
# Assuming you have OPENAI_API_KEY set in Streamlit secrets or environment
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- 4. Hugging Face Model Loaders (Enhanced with @st.cache_resource) ---
@st.cache_resource
def load_classifier_model():
    # Zero-shot classification is more flexible for custom topics
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

@st.cache_resource
def load_sentiment_model():
    # Using a sentiment analysis model for journal entries
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Load models once at app startup
classifier = load_classifier_model()
sentiment_analyzer = load_sentiment_model() # This was used in your previous journal code


# --- 5. Database Initialization and Schema Upgrade ---
# This ensures the DB connection is established and schema is up-to-date
# run_schema_upgrades() itself is decorated with @st.cache_resource in db.py
run_schema_upgrades()


# --- 6. Translation Functions ---
def translate_user_input(text, target_lang="en"):
    detected_lang = detect(text)
    if detected_lang != 'en':
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated, detected_lang
    return text, detected_lang

def translate_bot_response(text, target_lang):
    if target_lang != 'en':
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    return text

# --- 7. App Configuration ---
st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="wide")

# --- 8. Main Streamlit Application Function ---
# Encapsulating the UI logic ensures session state and DB calls are handled well
def main_app():
    # --- Session State Initialization ---
    # Moved inside main_app for clarity and proper re-initialization on full app restart
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_name' not in st.session_state: # Added for user display
        st.session_state.user_name = None
    if 'page' not in st.session_state:
        st.session_state.page = "Login" # Start at Login page


    st.sidebar.title("✝️ Tukuza Yesu Toolkit 🚀")

    # --- Login/User Management Section (Main Entry Point) ---
    if st.session_state.page == "Login":
        st.header("Welcome to Tukuza!")
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

        with login_tab:
            st.markdown("### Existing User Login")
            # Get connection and cursor right before use
            conn = get_db_connection()
            cursor = conn.cursor()
            # Fetch existing users to allow selection
            cursor.execute("SELECT id, name FROM user_profiles ORDER BY name")
            existing_users = cursor.fetchall()

            users = {row["name"]: row["id"] for row in existing_users}
            user_names = ["Select User"] + sorted(list(users.keys())) # Sort for better UX

            selected_user_name = st.selectbox("Select your profile", user_names)

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
        # Tool selector is now main navigation
        tool = st.sidebar.selectbox("🛠️ Select a Tool", [
            "🏠 Dashboard", # Added Dashboard as an option for clarity
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
            # You can add summary information here later if you want

        elif tool == "📖 BibleBot":
            biblebot_ui() # Calls the UI from modules/biblebot_ui.py

        elif tool == "📘 Spiritual Growth Tracker":
            # This is where your journaling and growth tracking UI would be
            # Assuming growth_tracker_ui handles all DB interaction internally
            growth_tracker_ui(sentiment_analyzer) # Pass sentiment_analyzer if it needs it

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
            # Pass classifier/sentiment_analyzer if needed by gift_assessment_ui
            gift_assessment_ui() # You'll need to update gift_assessment_ui to accept these
            # The original code for the gift assessment was quite long,
            # so it's best to move it into modules/gift_assessment.py entirely.
            # Below is a conceptual placeholder of what gift_assessment_ui might contain.

            # if "user_id" not in st.session_state or st.session_state.user_id is None:
            #     st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
            #     return # Exit the function if no user is logged in

            # current_user_id = st.session_state.user_id
            # conn = get_db_connection()
            # cursor = conn.cursor()

            # # Load models (moved inside if tool block for direct access by gift_assessment_ui)
            # model_path = os.path.join("models", "gift_model.pkl")
            # if not os.path.exists(model_path):
            #     st.error("Spiritual gifts model file not found. Please ensure 'gift_model.pkl' is in the 'models' directory.")
            #     st.stop() # Or return
            # model = joblib.load(model_path)

            # # The rest of your gift assessment logic goes here,
            # # including fetching previous results, the form, and saving.
            # # Ensure all DB calls within gift_assessment_ui get their own conn/cursor.
            # # e.g., conn = get_db_connection(); cursor = conn.cursor()
            # # This is why moving it to its own module and passing necessary data is cleaner.


# --- 9. Entry Point for the App ---
if __name__ == "__main__":
    main_app()

# --- 10. Credit (Always show) ---
st.markdown("---")
st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")