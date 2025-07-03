import streamlit as st
import openai
import random
import datetime
import requests
from langdetect import detect
from googletrans import Translator
import os

# ✅ NEW: create OpenAI client object for openai>=1.0.0
client = openai.OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
)

# Initialize translator
translator = Translator()

# --- Helper: Daily Verse ---
def get_daily_verse():
    verse_list = [
        "John 3:16", "Psalm 23:1", "Romans 8:28", "Philippians 4:13", "Isaiah 41:10",
        "Proverbs 3:5", "Jeremiah 29:11", "Psalm 46:1", "Matthew 11:28", "Genesis 1:1",
        "Hebrews 11:1", "1 Corinthians 13:4", "2 Timothy 1:7", "Romans 5:8", "James 1:5",
        "1 Peter 5:7", "Romans 10:9", "Isaiah 40:31", "Joshua 1:9", "Psalm 119:105"
    ]
    random.seed(datetime.date.today().toordinal())
    verse_ref = random.choice(verse_list)
    try:
        url = f"https://bible-api.com/{verse_ref.replace(' ', '%20')}"
        response = requests.get(url)
        data = response.json()
        return f"📖 *{verse_ref}* — {data.get('text', '').strip()}"
    except:
        return "📖 Verse of the Day unavailable."

# --- UI Setup ---
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("Tukuza Yesu BibleBot")
st.info(get_daily_verse())

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Input ---
raw_input = st.chat_input("🖋️ Ask your Bible question here (any language)...")
question = None
if raw_input:
    try:
        user_lang = detect(raw_input)
        if user_lang != "en":
            translated = translator.translate(raw_input, src=user_lang, dest="en")
            question = translated.text
        else:
            question = raw_input
    except:
        question = raw_input

# --- Response Logic ---
if question:
    with st.chat_message("user"):
        st.markdown(raw_input)

    try:
        # ✅ NEW CLIENT CALL for openai>=1.0.0
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Bible-based assistant. Respond with love, truth, and Scripture references."},
                {"role": "user", "content": question}
            ],
            stream=True,
        )
        with st.chat_message("assistant"):
            reply = st.write_stream(stream)
        st.session_state.messages.append({"role": "user", "content": raw_input})
        st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"💥 Error: {e}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
