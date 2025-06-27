import streamlit as st
from openai import OpenAI
import requests
import random
import datetime

# --- DAILY BIBLE VERSE ---
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

# --- PAGE SETUP ---
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.info(get_daily_verse())
st.subheader("Ask your Bible question below:")

# --- INPUT FIELD (DEFINED EARLY) ---
question = st.text_input("❓ Ask a Bible question (Swali lako):")

# --- OPENAI CLIENT ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- AI REPLY ---
if question:
    try:
        with st.spinner("🔍 Searching Scripture..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            answer = response.choices[0].message.content
            st.success(answer)
    except Exception as e:
        st.error(f"💥 Unexpected error:\n\n{str(e)}")

# --- FOOTER ---
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
