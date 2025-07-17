import streamlit as st
from openai import OpenAI # Assuming OpenAI client is used in biblebot_ui
import os
import joblib
import numpy as np
import pandas as pd
import sqlite3
# Removed unused imports if voice input is not actively used:
# from streamlit_webrtc import webrtc_streamer
# import av
# import queue
import sys
import json # Already imported, good for handling JSON serialization of lists

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.biblebot_ui import biblebot_ui # Assuming this module uses OpenAI

from langdetect import detect
from deep_translator import GoogleTranslator

# 🌍 Translation Functions
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

# 🎤 Voice Input Setup (Commented out if not actively used)
# audio_queue = queue.Queue()
# class AudioProcessor:
#     def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
#         audio_queue.put(frame.to_ndarray().flatten().astype("float32").tobytes())
#         return frame

# ---------------------------
# SQLite Setup
# ---------------------------
# Use st.cache_resource for efficient database connection management.
# This ensures the connection is only created once and reused across reruns.
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("discipleship_agent.db", check_same_thread=False)
    # Set row_factory to sqlite3.Row for dictionary-like access to rows
    # conn.row_factory = sqlite3.Row # Uncomment if you prefer dict-like access
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE, -- Added UNIQUE constraint for name
    stage TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS gift_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    primary_gift TEXT,
    secondary_gift TEXT,
    primary_role TEXT,
    secondary_role TEXT,
    ministries TEXT, -- Stored as JSON string
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS growth_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry TEXT,
    reflection TEXT,
    goal TEXT,
    mood TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(id)
)
""")
conn.commit() # Commit table creations

# ---------------------------
# App Config
# ---------------------------
st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="wide")

# 🔐 User Management (Login/Registration UI)
if "user_id" not in st.session_state:
    st.subheader("👤 Login or Create Your Discipleship Profile")

    login_tab, register_tab = st.tabs(["Login", "Register New Profile"])

    with login_tab:
        st.markdown("### Existing User Login")
        # Fetch existing users to allow selection
        cursor.execute("SELECT id, name FROM user_profiles ORDER BY name")
        existing_users = cursor.fetchall()
        
        if existing_users:
            user_options = {name: uid for uid, name in existing_users}
            selected_name = st.selectbox("Select Your Name", options=list(user_options.keys()), key="login_name_select")
            if st.button("🚪 Login", key="login_button"):
                st.session_state.user_id = user_options[selected_name]
                st.success(f"Logged in as {selected_name}!")
                st.rerun()
        else:
            st.info("No profiles found. Please register a new profile.")

    with register_tab:
        st.markdown("### Register New Profile")
        reg_name = st.text_input("Your Name", key="register_profile_name_input")
        reg_stage = st.selectbox("Your Faith Stage", [
            "New Believer", "Growing Disciple", "Ministry Ready", "Faith Leader"
        ], key="register_profile_stage_select")

        if st.button("✅ Create Profile", key="create_profile_button"):
            if reg_name.strip() == "":
                st.warning("Please enter your name to create a profile.")
            else:
                try:
                    cursor.execute("INSERT INTO user_profiles (name, stage) VALUES (?, ?)", (reg_name, reg_stage))
                    conn.commit()
                    st.session_state.user_id = cursor.lastrowid
                    st.success(f"Profile for {reg_name} created and logged in!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"A profile with the name '{reg_name}' already exists. Please choose a different name or log in.")

else:
    user_id = st.session_state.user_id
    cursor.execute("SELECT name, stage FROM user_profiles WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        st.session_state.user_profile = {"name": user_data[0], "stage": user_data[1]} # Load profile into session state
        col1, col2 = st.columns([2, 1])
        with col1:
            st.success(f"Welcome back, **{user_data[0]}** – {user_data[1]}")
        with col2:
            # Added a logout button for convenience
            if st.button("↩️ Logout", key="logout_button"):
                st.session_state.pop("user_id", None)
                st.session_state.pop("user_profile", None)
                st.info("Logged out successfully.")
                st.rerun()
            st.markdown("<div style='text-align:right'>🧭 Profile loaded</div>", unsafe_allow_html=True)
    else:
        # Handle case where user_id in session_state doesn't match a DB record (e.g., DB reset)
        st.session_state.pop("user_id", None)
        st.session_state.pop("user_profile", None)
        st.warning("User profile not found. Please create a new one.")
        st.rerun()


# ---------------------------
# Sidebar Navigation
# ---------------------------
st.markdown("### ✝️ Tukuza Yesu Toolkit")
tool = st.selectbox("🛠️ Select a Tool", [
    "📖 BibleBot",
    "📘 Spiritual Growth Tracker", # Moved up for logical flow as it's a new feature
    "🔖 Verse Classifier",
    "🌅 Daily Verse",
    "🧪 Spiritual Gifts Assessment"
], index=0, key="tool_selector")

# ---------------------------
# Tool Sections (using a consistent if/elif structure)
# ---------------------------
if tool == "📖 BibleBot":
    biblebot_ui()

elif tool == "📘 Spiritual Growth Tracker":
    if "user_id" not in st.session_state:
        st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
        st.stop()

    st.subheader("📘 Spiritual Growth Journal")
    st.markdown("### 📝 New Journal Entry")

    with st.form("growth_journal_form", clear_on_submit=True):
        entry = st.text_area("✍️ What did God teach you today?", key="growth_entry")
        reflection = st.text_area("💭 Any reflections, struggles, or encouragement?", key="growth_reflection")
        goal = st.text_input("🎯 Set a goal for your spiritual walk this week", key="growth_goal")
        mood = st.selectbox("😌 Mood", ["😊 Joyful", "🙏 Thankful", "😢 Heavy", "😐 Neutral", "💪 Empowered"], key="growth_mood")

        submitted = st.form_submit_button("📌 Save Entry") # Added key

        if submitted:
            if entry.strip() == "":
                st.warning("Please write something in your journal entry.")
            else:
                cursor.execute("""
                    INSERT INTO growth_journal (user_id, entry, reflection, goal, mood)
                    VALUES (?, ?, ?, ?, ?)
                """, (st.session_state.user_id, entry, reflection, goal, mood))
                conn.commit()
                st.success("✅ Journal entry saved!")
                st.rerun()

    # Show past entries
    st.markdown("### 📚 Your Past Journal Entries")
    cursor.execute("""
        SELECT id, entry, reflection, goal, mood, timestamp
        FROM growth_journal
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (st.session_state.user_id,))
    journal_entries = cursor.fetchall()

    if journal_entries:
        for i, (entry_id, entry, reflection, goal, mood, timestamp) in enumerate(journal_entries, 1):
            with st.expander(f"📖 Entry #{i} – {timestamp}"):
                st.markdown(f"**Mood:** {mood}")
                st.markdown(f"**Entry:** {entry}")
                st.markdown(f"**Reflection:** {reflection}")
                st.markdown(f"**Goal:** {goal}")

                if st.button(f"❌ Delete Entry #{entry_id}", key=f"delete_journal_entry_{entry_id}"): # Unique key for delete button
                    cursor.execute("DELETE FROM growth_journal WHERE id = ?", (entry_id,))
                    conn.commit()
                    st.success("Entry deleted!")
                    st.rerun()
    else:
        st.info("No journal entries yet. Start by adding a new entry above!")


elif tool == "🔖 Verse Classifier":
    st.subheader("Classify a Bible Verse")

    model_path = os.path.join("models", "model.pkl")
    vectorizer_path = os.path.join("models", "vectorizer.pkl")

    if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
        st.error("Model files not found. Please ensure 'model.pkl' and 'vectorizer.pkl' are in the 'models' directory.")
        st.stop()

    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    st.write("🧠 Model can detect these topics:", model.classes_)

    verse = st.text_area("Paste a Bible verse here:", key="verse_classifier_input")
    if st.button("Classify", key="classify_button"):
        if verse.strip() == "":
            st.warning("Please enter a verse.")
        else:
            X = vectorizer.transform([verse])
            prediction = model.predict(X)[0]
            st.success(f"🧠 Detected Topic: **{prediction}**")

elif tool == "🌅 Daily Verse":
    st.subheader("🌞 Your Daily Verse")
    verse = "“This is the day that the Lord has made; let us rejoice and be glad in it.” – Psalm 118:24"
    st.success(verse)

elif tool == "🧪 Spiritual Gifts Assessment":
    if "user_id" not in st.session_state:
        st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
        st.stop()

    # Load models
    model_path = os.path.join("models", "gift_model.pkl")
    if not os.path.exists(model_path):
        st.error("Spiritual gifts model file not found. Please ensure 'gift_model.pkl' is in the 'models' directory.")
        st.stop()
    model = joblib.load(model_path)

    current_user_id = st.session_state.user_id

    # Try to retrieve existing gift results from the database
    cursor.execute("SELECT primary_gift, secondary_gift, primary_role, secondary_role, ministries FROM gift_assessments WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (current_user_id,))
    db_gift_results = cursor.fetchone()

    if db_gift_results:
        # Reconstruct the dictionary from DB tuple
        gr = {
            "primary": db_gift_results[0],
            "secondary": db_gift_results[1],
            "primary_role": db_gift_results[2],
            "secondary_role": db_gift_results[3],
            "ministries": json.loads(db_gift_results[4]) if db_gift_results[4] else [] # Deserialize JSON
        }
        
        st.markdown("### 💡 Your Last Spiritual Gift Assessment")
        st.info(f"""
        - 🧠 Primary Gift: **{gr.get('primary', 'N/A')}** ({gr.get('primary_role', 'N/A')})
        - 🌟 Secondary Gift: **{gr.get('secondary', 'N/A')}** ({gr.get('secondary_role', 'N/A')})
        """)
        st.markdown("### 🚀 Suggested Ministry Pathways")
        for i, role in enumerate(gr.get("ministries", []), 1):
            st.markdown(f"- {i}. **{role}**")

        col_buttons_1, col_buttons_2 = st.columns(2)
        with col_buttons_1:
            # Prepare content for download
            report_content = f"""
Tukuza Yesu Spiritual Gifts Assessment Report

User Name: {st.session_state.user_profile.get('name', 'N/A')}
Faith Stage: {st.session_state.user_profile.get('stage', 'N/A')}

---

Your Spiritual Gift Assessment Results:

🧠 Primary Spiritual Gift: {gr.get('primary', 'N/A')} ({gr.get('primary_role', 'N/A')})
🌟 Secondary Spiritual Gift: {gr.get('secondary', 'N/A')} ({gr.get('secondary_role', 'N/A')})

---

🚀 Suggested Ministry Pathways:
"""
            for i, role in enumerate(gr.get("ministries", []), 1):
                report_content += f"- {i}. {role}\n"

            report_content += """
---
"So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers..." – Ephesians 4:11

Built with faith by Sammy Karuri ✡ | Tukuza Yesu AI Toolkit 🌐
"""
            st.download_button(
                label="⬇️ Download Your Gift Report",
                data=report_content,
                file_name=f"tukuza_spiritual_gifts_report_{st.session_state.user_profile.get('name', 'user').replace(' ', '_').lower()}.txt",
                mime="text/plain",
                key="download_gift_report_button"
            )
        with col_buttons_2:
            if st.button("🧹 Clear Previous Gift Assessment", key="clear_gift_assessment_button"):
                cursor.execute("DELETE FROM gift_assessments WHERE user_id = ?", (current_user_id,))
                conn.commit()
                st.rerun()
        
        st.stop()

    # If no results in DB, display the assessment form
    st.subheader("🧪 Spiritual Gifts Assessment")

    sample_input = st.text_input("🌐 Type anything in your language to personalize the experience:", key="sample_lang_input_assessment")

    SUPPORTED_LANG_CODES = list(GoogleTranslator().get_supported_languages(as_dict=True).values())

    user_lang = "en"
    if sample_input.strip():
        try:
            detected = detect(sample_input)
            if detected in SUPPORTED_LANG_CODES:
                user_lang = detected
            else:
                st.warning(f"⚠️ Language '{detected}' not supported. Defaulting to English.")
        except:
            user_lang = "en"

    questions_en = [
        "I enjoy explaining Bible truths in a clear, structured way.",
        "I naturally take the lead when organizing ministry activities.",
        "I feel driven to share the gospel with strangers.",
        "I often sense spiritual warnings or encouragements for others.",
        "I easily feel compassion for people who are suffering.",
        "I enjoy giving resources to help others, even when it costs me.",
        "I’m happiest when working behind the scenes to help others.",
        "People often ask for my advice in complex spiritual matters.",
        "I enjoy studying and understanding deep biblical concepts.",
        "I trust God even in situations where others worry.",
        "I can often sense when something is spiritually wrong or deceptive.",
        "I enjoy hosting people and making them feel welcome.",
        "I often feel led to pray for others, even for long periods.",
        "I’m concerned about the spiritual growth of those around me.",
        "I naturally uplift others who are discouraged or unsure.",
        "I’ve prayed for people and seen them emotionally or physically healed.",
        "I enjoy pioneering new ministries or reaching unreached people.",
        "I enjoy managing projects and keeping people on track.",
        "I have spoken in a spiritual language not understood by others.",
        "I can understand and explain messages spoken in tongues.",
        "I stand firm in my faith even in hostile or public settings.",
        "I prepare lessons that help people grow in their faith.",
        "I look for ways to bring spiritual truth into everyday conversations.",
        "I cry or feel deeply moved when others are in pain.",
        "I often give above my tithe when I see a need.",
        "I influence others toward a vision in ministry.",
        "I can distinguish between truth and error without visible signs.",
        "I’ve had dreams, impressions, or messages that turned out accurate.",
        "I take personal responsibility for the spiritual welfare of others.",
        "I write or speak encouraging words that impact others deeply."
    ]

    gift_to_fivefold = {
        "Teaching": "Teacher",
        "Prophecy": "Prophet",
        "Evangelism": "Evangelist",
        "Service": "Pastor",
        "Giving": "Pastor",
        "Mercy": "Pastor",
        "Leadership": "Apostle"
    }

    questions = questions_en
    if user_lang != "en":
        try:
            questions = [GoogleTranslator(source="en", target=user_lang).translate(q) for q in questions_en]
        except:
            st.warning("⚠️ Translation failed. Using English.")

    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        try:
            scale_instruction = GoogleTranslator(source='en', target=user_lang).translate(scale_instruction)
        except:
            pass
    st.caption(scale_instruction)

    with st.form("gift_assessment_form", clear_on_submit=True):
        responses = [st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_slider_{i}") for i, q in enumerate(questions)]

        submit_text = "🎯 Discover My Spiritual Gift"
        if user_lang != "en":
            try:
                submit_text = GoogleTranslator(source="en", target=user_lang).translate(submit_text)
            except:
                pass

        submitted = st.form_submit_button(submit_text) # Added a unique key

        if submitted:
            try:
                input_data = pd.DataFrame([responses], columns=[f"Q{i+1}" for i in range(len(responses))])
                probs = model.predict_proba(input_data)[0]
                top2 = np.argsort(probs)[-2:][::-1]

                primary = model.classes_[top2[0]]
                secondary = model.classes_[top2[1]]

                primary_role = gift_to_fivefold.get(primary, "Undetermined")
                secondary_role = gift_to_fivefold.get(secondary, "Undetermined")

                gift_ministry_map = {
                    "Teaching": ["Bible Study Leader", "Discipleship Coach", "Apologist"],
                    "Prophecy": ["Intercessor", "Prophetic Mentor", "Watchman"],
                    "Evangelism": ["Street Evangelist", "Mission Worker", "Church Planter"],
                    "Service": ["Church Operations", "Setup Crew", "Admin Support"],
                    "Mercy": ["Counselor", "Hospital Chaplain", "Comfort Ministry"],
                    "Giving": ["Donor Relations", "Fundraising Coordinator", "Business-as-Mission"],
                    "Leadership": ["Ministry Director", "Visionary Leader", "Team Builder"]
                }

                def recommend_ministries(primary, secondary, gift_map):
                    return list(set(gift_map.get(primary, []) + gift_map.get(secondary, [])))[:3]

                ministry_suggestions = recommend_ministries(primary, secondary, gift_ministry_map)

                cursor.execute("""
                    INSERT INTO gift_assessments (user_id, primary_gift, secondary_gift, primary_role, secondary_role, ministries)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    current_user_id,
                    primary,
                    secondary,
                    primary_role,
                    secondary_role,
                    json.dumps(ministry_suggestions)
                ))
                conn.commit()
                
                st.success("Your assessment has been saved!")
                st.rerun()

            except Exception as e:
                st.error(f"⚠️ Error during prediction or saving: {e}")

# ---------------------------
# © Credit - Always show
# ---------------------------
st.markdown("---")
st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")