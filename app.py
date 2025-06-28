import streamlit as st
import openai
import random
import datetime
import requests

# Set your API key from Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
        return f"\ud83d\udcd6 *{verse_ref}* \u2014 {data.get('text', '').strip()}"
    except:
        return "\ud83d\udcd6 Verse of the Day unavailable."

# --- UI Setup ---
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="book")
st.title("Tukuza Yesu BibleBot")
def get_daily_verse():
    return "📖 John 3:16 — For God so loved the world..."
st.info(get_daily_verse())

# --- Chat logic ---
question = None  # placeholder to avoid NameError

# Collect user input from chat box
typed = st.chat_input("Type your Bible question here...")
if typed:
    question = typed

# Placeholder for future voice input
# Example:
# if st.button("\ud83c\udfa4 Use Microphone"):
#     question = recognize_from_queue()  # if you implement mic logic

# Only run OpenAI if we have a valid question
if question:
    with st.chat_message("user"):
        st.markdown(question)

    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Bible-based assistant."},
                {"role": "user", "content": question}
            ],
            stream=True,
        )
        with st.chat_message("assistant"):
            reply = st.write_stream(stream)
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"\ud83d\udca5 Unexpected error: {e}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "\u271d\ufe0f Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
