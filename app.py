import streamlit as st
import openai
import random
import datetime
import requests

def get_daily_verse():
    import random, datetime, requests  # optional safety
    # Use today’s date to generate a consistent verse each day
    random.seed(datetime.date.today().toordinal())
    
    # Example: Choose from 20 popular verse references
    verse_list = [
        "John 3:16", "Psalm 23:1", "Romans 8:28", "Philippians 4:13", "Isaiah 41:10",
        "Proverbs 3:5", "Jeremiah 29:11", "Psalm 46:1", "Matthew 11:28", "Genesis 1:1",
        "Hebrews 11:1", "1 Corinthians 13:4", "2 Timothy 1:7", "Romans 5:8", "James 1:5",
        "1 Peter 5:7", "Romans 10:9", "Isaiah 40:31", "Joshua 1:9", "Psalm 119:105"
    ]
    today_verse = random.choice(verse_list)
    
    # Fetch from Bible API
    url = f"https://bible-api.com/{today_verse.replace(' ', '%20')}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return f"📖 *{today_verse}* — {data.get('text', '').strip()}"
    except:
        return "📖 Verse of the Day unavailable at the moment."

# ✅ Set your API key from Streamlit Cloud secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.subheader("Ask your question below:")

# ✅ Call daily verse display here
st.info(get_daily_verse())
question = st.text_input("❓ Ask a Bible question (Swali lako):")

if question:
    try:
        with st.spinner("Answering..."):
            # ✅ Correct API call for OpenAI v1.x
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            # ✅ Proper way to access content in v1.x
            st.success(response.choices[0].message.content)
    except Exception as e:
        st.error(f"💥 Unexpected error:\n\n{str(e)}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
