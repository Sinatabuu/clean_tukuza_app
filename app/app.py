import streamlit as st
from openai import OpenAI
import os
import joblib
import numpy as np
import pandas as pd
from streamlit_webrtc import webrtc_streamer
import av
import queue
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.biblebot_ui import biblebot_ui # Ensure this file is also updated!
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

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", key="profile_name_input")
    with col2:
        stage = st.selectbox("Your Faith Stage", [
            "New Believer", "Growing Disciple", "Ministry Ready", "Faith Leader"
        ], key="profile_stage_select")

    if st.button("✅ Save Profile", key="save_profile_button"):
        st.session_state.user_profile = {
            "name": name,
            "stage": stage,
            "history": []
        }
        st.success("Profile created for this session!")
        st.experimental_rerun()

elif "user_profile" in st.session_state:
    profile = st.session_state.user_profile
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"Welcome back, {profile['name']} – {profile['stage']}")
    with col2:
        st.markdown("<div style='text-align:right'>🧭 Profile loaded</div>", unsafe_allow_html=True)

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.markdown("### ✝️ Tukuza Yesu Toolkit")
tool = st.selectbox("🛠️ Select a Tool", [
    "📖 BibleBot",
    "🔖 Verse Classifier",
    "🌅 Daily Verse",
    "🧪 Spiritual Gifts Assessment"
], index=0, key="tool_selector")

# ---------------------------
# 1. BibleBot
# ---------------------------
if tool == "📖 BibleBot":
    biblebot_ui()

# ---------------------------
# 2. Verse Classifier
# ---------------------------
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
    st.warning("This module is under maintenance. Please check back later.")

# ---------------------------
# © Credit - Always show
# ---------------------------
st.markdown("---")
st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")
