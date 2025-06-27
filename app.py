import streamlit as st
import openai
import random
import datetime
import requests
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import queue

# Setup OpenAI key
from openai import OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if question:
    try:
        with st.spinner("Answering..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            st.success(response.choices[0].message.content)
    except Exception as e:
        st.error(f"💥 Unexpected error:\n\n{str(e)}")

# 🎯 Function to fetch daily Bible verse
def get_daily_verse():
    verse_list = [
        "John 3:16", "Psalm 23:1", "Romans 8:28", "Philippians 4:13", "Isaiah 41:10",
        "Proverbs 3:5", "Jeremiah 29:11", "Psalm 46:1", "Matthew 11:28", "Genesis 1:1",
        "Hebrews 11:1", "1 Corinthians 13:4", "2 Timothy 1:7", "Romans 5:8", "James 1:5",
        "1 Peter 5:7", "Romans 10:9", "Isaiah 40:31", "Joshua 1:9", "Psalm 119:105"
    ]
    random.seed(datetime.date.today().toordinal())
    verse = random.choice(verse_list)
    url = f"https://bible-api.com/{verse.replace(' ', '%20')}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        return f"📖 *{verse}* — {data.get('text', '').strip()}"
    except:
        return "📖 Verse of the Day unavailable."

# 🎙 Audio processor class for mic input
audio_q = queue.Queue()

class AudioProcessor:
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray().flatten().astype(np.int16).tobytes()
        audio_q.put(audio)
        return frame

# 🔧 Page setup
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.info(get_daily_verse())
st.subheader("Ask by text or by voice:")

# Session memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# 💬 Text input
typed = st.chat_input("Type your Bible question here (Swali lako)...")
if typed:
    st.session_state.messages.append({"role": "user", "content": typed})

# 🎙 Mic button
webrtc_ctx = webrtc_streamer(
    key="mic",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)


# Transcribe button
if st.button("🎙️ Transcribe & Ask from Mic"):
    recognizer = sr.Recognizer()
    try:
        audio_data = sr.AudioData(b"".join(list(audio_q.queue)), 16000, 2)
        voice_question = recognizer.recognize_google(audio_data)
        st.success(f"🗣 You said: {voice_question}")
        st.session_state.messages.append({"role": "user", "content": voice_question})
    except sr.UnknownValueError:
        st.error("Sorry, couldn't understand your voice.")
    except sr.RequestError:
        st.error("Speech recognition service failed.")

# Show full chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Send last question to GPT
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        try:
            stream = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )
            reply = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"💥 Unexpected error:\n\n{str(e)}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
