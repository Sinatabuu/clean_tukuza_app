# 📦 MODULE: biblebot_ui.py
import streamlit as st
from openai import OpenAI
from langdetect import detect
from deep_translator import GoogleTranslator
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except Exception:
    sr = None
    SR_AVAILABLE = False

import os


def biblebot_ui():
    # ✅ Setup OpenAI Client
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment.")
        return

    client = OpenAI(api_key=api_key)

    # 📖 Title and caption
    st.subheader("📖 BibleBot (Multilingual + Voice)")
    st.caption("🙋 Ask anything related to the Bible — type or speak")

    if "messages" not in st.session_state:
        st.session_state.messages = []

   
    # -------------------------
# 📥 Input + 🎙️ Mic in Same Row
# -------------------------
    col1, col2 = st.columns([7, 1])
    with col1:
        user_input = st.text_input("Ask your question:", key="text_question")

    with col2:
        if SR_AVAILABLE:
            mic_clicked = st.button("🎙️", key="mic_button")
        else:
            st.button("🎙️", key="mic_button_disabled", disabled=True)
            mic_clicked = False

        # 🎤 Handle voice if mic is clicked
    if mic_clicked:
        if not SR_AVAILABLE:
            st.info("Voice input isn’t available on this deployment.")
        else:
            try:
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    st.info("🎤 Listening…")
                    audio = recognizer.listen(source, timeout=5)
                voice_text = recognizer.recognize_google(audio)
                st.success(f"🗣️ Recognized: {voice_text}")
                st.session_state.messages.append({"role": "user", "content": voice_text})
            except Exception as e:
                st.error(f"Voice error: {e}")


    # 📝 Handle text input
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

    # 🔁 Translate and Process
    if st.session_state.messages:
        translated_messages = []
        original_lang = None

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                detected_lang = detect(msg["content"])
                original_lang = detected_lang
                if detected_lang != 'en':
                    translated = GoogleTranslator(source='auto', target='en').translate(msg["content"])
                else:
                    translated = msg["content"]
                translated_messages.append({"role": "user", "content": translated})
            else:
                translated_messages.append(msg)

        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=translated_messages,
                stream=True,
            )

            with st.chat_message("user"):
                st.markdown(st.session_state.messages[-1]["content"])

            with st.chat_message("assistant"):
                reply = st.write_stream(stream)

            if original_lang and original_lang != 'en':
                reply = GoogleTranslator(source='en', target=original_lang).translate(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
