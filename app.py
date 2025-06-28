import streamlit as st
import openai
import random
import datetime
import requests
from langdetect import detect
from googletrans import Translator

# Initialize translation tool
translator = Translator()

# Set your API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

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
        return f"\U0001F4D6 *{verse_ref}* — {data.get('text', '').strip()}"
    except:
        return "\U0001F4D6 Verse of the Day unavailable."

# --- UI Setup ---
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("Tukuza Yesu BibleBot")
st.info(get_daily_verse())

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Multilingual Input ---
raw_input = st.chat_input("🖋️ Type your Bible question here (any language)...")
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
        question = raw_input  # Fallback if detection fails

# --- Chat Completion ---
if question:
    with st.chat_message("user"):
        st.markdown(raw_input)

    try:
        stream = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Bible-based assistant."},
                {"role": "user", "content": question}
            ],
            stream=True,
        )
        with st.chat_message("assistant"):
            reply = st.write_stream(stream)
        st.session_state.messages.append({"role": "user", "content": raw_input})
        st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"💥 Unexpected error: {e}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
