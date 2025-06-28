import streamlit as st
import openai
from streamlit_webrtc import webrtc_streamer
import speech_recognition as sr
import av
import queue

question = None  # Always define first

# Then fill it from input or voice
question = st.chat_input("Or type your Bible question here:")

# Or after transcribing mic:
if st.button("📝 Transcribe Mic Input"):
    question = recognize_from_queue()
    st.success(f"📝 Transcribed: {question}")

# Now it’s safe to check:
if question:
    ...

# 🔐 API key input
openai_api_key = st.text_input("🔑 Enter your OpenAI API key:")
if not openai_api_key:
    st.warning("Please enter your key to continue.")
    st.stop()

client = openai.OpenAI(api_key=openai_api_key)

# Set page config
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.caption("🎙 Ask by speaking or typing your Bible question")

# Store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🧠 For audio recording
audio_queue = queue.Queue()

class AudioProcessor:
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray().flatten().astype("float32").tobytes()
        audio_queue.put(audio)
        return frame

# 🎤 Microphone streaming
webrtc_ctx = webrtc_streamer(
    key="mic",
    mode="SENDONLY",
    in_audio=True,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

def recognize_from_queue():
    recognizer = sr.Recognizer()
    try:
        audio_data = sr.AudioData(b"".join(list(audio_queue.queue)), 16000, 2)
        return recognizer.recognize_google(audio_data)
    except:
        return "Sorry, I couldn't understand the audio."

# Chat interface with arrow submit button
with st.form("chat_form"):
    question = st.text_input("✍️ Type your Bible question:", placeholder="➡️ What does the Bible say about grace?")
    send = st.form_submit_button("➡️ Send")

# Transcribe Mic Input
if st.button("🎤 Transcribe Mic Input"):
    question = recognize_from_queue()
    st.success(f"📝 Transcribed: {question}")
    send = True

# If form was submitted or voice used
if send and question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
    )

    with st.chat_message("assistant"):
        reply = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": reply})
