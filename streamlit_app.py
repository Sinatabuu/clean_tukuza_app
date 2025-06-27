import streamlit as st
import speech_recognition as sr
from openai import OpenAI
import os

# 🔑 Ask user for their API key
openai_api_key = st.text_input("🔐 Enter your OpenAI API key:", type="password")
if not openai_api_key:
    st.warning("🗝️ Please enter your API key to continue.")
    st.stop()

# ✅ OpenAI client
client = OpenAI(api_key=openai_api_key)

st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.caption("✝️ Ask questions by typing or uploading your voice.")

# 🧠 Chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🔊 Voice transcription function
def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, couldn't understand the audio."
    except sr.RequestError:
        return "Speech recognition service error."

# 📥 Voice input
uploaded_audio = st.file_uploader("🎙️ Upload a WAV file to ask by voice", type=["wav"])
question = None

if uploaded_audio:
    with open("temp.wav", "wb") as f:
        f.write(uploaded_audio.getbuffer())
    st.audio("temp.wav", format="audio/wav")
    st.info("Transcribing audio...")
    question = transcribe_audio("temp.wav")
    st.success(f"📝 Transcribed: {question}")

# ⌨️ Text input
if not question:
    question = st.chat_input("Type your Bible question...")

# 🔄 Run chat if there’s a question
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
