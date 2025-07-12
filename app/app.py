import streamlit as st
from openai import OpenAI
import os
import joblib
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av
import queue
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.biblebot_ui import biblebot_ui # Ensure this file is also updated!

# 🌍 Translation Functions (Imports are inside for lazy loading, which is fine)
def translate_user_input(text, target_lang="en"):
    from langdetect import detect
    from deep_translator import GoogleTranslator
    detected_lang = detect(text)
    if detected_lang != 'en':
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated, detected_lang
    return text, detected_lang

def translate_bot_response(text, target_lang):
    from deep_translator import GoogleTranslator
    if target_lang != 'en':
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    return text

# 🎤 Voice Input Setup
audio_queue = queue.Queue()

class AudioProcessor:
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio_queue.put(frame.to_ndarray().flatten().astype("float32").tobytes())
        return frame

# ---------------------------
# App Config
# ---------------------------
st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="wide")

# 🔐 Session-based user profile
if "user_profile" not in st.session_state:
    st.subheader("👤 Create Your Discipleship Profile")

    # --- ADDED UNIQUE KEYS TO PROFILE WIDGETS ---
    name = st.text_input("Your Name", key="profile_name_input")
    age = st.number_input("Your Age", min_value=10, max_value=100, step=1, key="profile_age_input")
    stage = st.selectbox("Your Faith Stage", [
        "New Believer", "Growing Disciple", "Ministry Ready", "Faith Leader"
    ], key="profile_stage_select")

    if st.button("✅ Save Profile", key="save_profile_button"): # Added key here
        st.session_state.user_profile = {
            "name": name,
            "age": age,
            "stage": stage,
            "history": []
        }
        st.success("Profile created for this session!")

elif "user_profile" in st.session_state:
    profile = st.session_state.user_profile
    st.success(f"Welcome back, {profile['name']} – {profile['stage']}")
    # st.json(profile)  # Removed for clean UI

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.markdown("### ✝️ Tukuza Yesu Toolkit")
tool = st.selectbox("🛠️ Select a Tool", [
    "📖 BibleBot",
    "🔖 Verse Classifier",
    "🌅 Daily Verse",
    "🧪 Spiritual Gifts Assessment"
], index=0, key="tool_selector") # Added key to selectbox

# ---------------------------
# 1. BibleBot (Ensure biblebot_ui.py is updated separately!)
# ---------------------------
if tool == "📖 BibleBot":
    biblebot_ui()

# ---------------------------
# 2. Verse Classifier
# ---------------------------
elif tool == "🔖 Verse Classifier":
    st.subheader("Classify a Bible Verse")

    model_path = os.path.join("models", "model.pkl")  # ✅ correct model
    vectorizer_path = os.path.join("models", "vectorizer.pkl")

    # Ensure models exist before loading
    if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
        st.error("Model files not found. Please ensure 'model.pkl' and 'vectorizer.pkl' are in the 'models' directory.")
        return # Exit to prevent further errors if models are missing
        
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    st.write("🧠 Model can detect these topics:", model.classes_)

    verse = st.text_area("Paste a Bible verse here:", key="verse_classifier_input") # Added key
    if st.button("Classify", key="classify_button"): # Added key here
        if verse.strip() == "":
            st.warning("Please enter a verse.")
        else:
            X = vectorizer.transform([verse])
            prediction = model.predict(X)[0]
            st.success(f"🧠 Detected Topic: **{prediction}**")

# ---------------------------
# 3. Daily Verse
# ---------------------------
elif tool == "🌅 Daily Verse":
    st.subheader("🌞 Your Daily Verse")
    verse = "“This is the day that the Lord has made; let us rejoice and be glad in it.” – Psalm 118:24"
    st.success(verse)

# ---------------------------
# 4. Spiritual Gifts Assessment
# ---------------------------
elif tool == "🧪 Spiritual Gifts Assessment":
    from deep_translator import GoogleTranslator
    from langdetect import detect

    model_path = os.path.join("models", "gift_model.pkl")
    if not os.path.exists(model_path):
        st.error("Spiritual gifts model file not found. Please ensure 'gift_model.pkl' is in the 'models' directory.")
        return # Exit if model is missing

    model = joblib.load(model_path)

    st.subheader("🧪 Spiritual Gifts Assessment")

    sample_input = st.text_input("🌐 Type anything in your language to personalize the experience (e.g. 'Yesu ni Bwana'):", key="sample_lang_input") # Added key

    if sample_input:
        try:
            user_lang = detect(sample_input)
        except: # Catching all exceptions for language detection issues
            user_lang = "en"
    else:
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

    if user_lang != "en":
        questions = [GoogleTranslator(source="en", target=user_lang).translate(q) for q in questions_en]
    else:
        questions = questions_en

    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        scale_instruction = GoogleTranslator(source='en', target=user_lang).translate(scale_instruction)
    st.caption(scale_instruction)

    with st.form("gift_assessment_form", clear_on_submit=True): # Added clear_on_submit for forms
        # --- ADDED UNIQUE KEYS TO SLIDERS ---
        responses = [st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_question_slider_{i}") for i, q in enumerate(questions)]

        submit_text = "🎯 Discover My Spiritual Gift"
        if user_lang != "en":
            submit_text = GoogleTranslator(source='en', target=user_lang).translate(submit_text)

        submitted = st.form_submit_button(submit_text, key="submit_gift_assessment_button") # Added key here

    if submitted:
        try:
            input_data = np.array(responses).reshape(1, -1)
            prediction = model.predict(input_data)[0]
            role = gift_to_fivefold.get(prediction, "Undetermined")

            result_msg = f"🧠 Your dominant spiritual gift is: {prediction}"
            role_msg = f"👑 This aligns with the Fivefold Ministry Role: {role}"
            verse_msg = "✝️ 'So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers...' – Ephesians 4:11"

            if user_lang != "en":
                result_msg = GoogleTranslator(source="en", target=user_lang).translate(result_msg)
                role_msg = GoogleTranslator(source="en", target=user_lang).translate(role_msg)
                verse_msg = GoogleTranslator(source="en", target=user_lang).translate(verse_msg)

            st.success(result_msg)
            st.info(role_msg)
            st.markdown(verse_msg)

        except Exception as e:
            st.error(f"⚠️ Error during prediction: {e}")

# ---------------------------
# © Credit - Always show
# ---------------------------
st.markdown("---")
st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")