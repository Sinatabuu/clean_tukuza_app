import streamlit as st
import openai
from streamlit_webrtc import webrtc_streamer
import speech_recognition as sr
import av
import queue

# 🔐 API key input
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set page config
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.caption("🎙 Ask by speaking or typing your Bible question")

# Store chat
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
from streamlit_webrtc import webrtc_streamer, WebRtcMode

webrtc_ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

# 🧠 Chat logic
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        stream=True,
    )

    with st.chat_message("assistant"):
        reply = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": reply})
