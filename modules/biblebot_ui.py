# 📦 MODULE: biblebot_ui.py
import streamlit as st
from openai import OpenAI
from langdetect import detect
from deep_translator import GoogleTranslator
import speech_recognition as sr
import os

def biblebot_ui():
    # ✅ API Setup
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment.")
        return
    client = OpenAI(api_key=api_key)

    # ✅ Section: Title + Model
    st.subheader("📖 BibleBot – Ask the Bible")
    st.caption("🌍 Type or speak in any language. Powered by AI & translation.")

    model_choice = st.selectbox("🤖 Choose Model", ["gpt-3.5-turbo", "gpt-4"])
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 🎙️ Voice + Input in One Row
    col1, col2 = st.columns([9, 1])
    with col1:
        user_input = st.text_input("", placeholder="Type or speak your Bible question...", key="biblebot_input")
    with col2:
        mic_clicked = st.button("🎙️", key="biblebot_mic")

    # 🎤 Voice Input
    if mic_clicked:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                st.info("🎙 Listening...")
                audio = recognizer.listen(source, timeout=5)
                voice_text = recognizer.recognize_google(audio)
                user_input = voice_text
            except sr.UnknownValueError:
                st.warning("⚠️ Could not understand.")
                return
            except Exception as e:
                st.error(f"🎙️ Error: {e}")
                return

    # 🧠 Process input
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        try:
            detected_lang = detect(user_input)
            input_en = GoogleTranslator(source='auto', target='en').translate(user_input) if detected_lang != 'en' else user_input

            # 💬 Query OpenAI
            stream = client.chat.completions.create(
                model=model_choice,
                messages=[{"role": "user", "content": input_en}],
                stream=True,
            )

            # 👤 Show user input
            with st.chat_message("user"):
                st.markdown(user_input)

            # 🤖 Show assistant output
            with st.chat_message("assistant"):
                reply_container = st.empty()
                reply = ""
                for chunk in stream:
                    part = chunk.choices[0].delta.content or ""
                    reply += part
                    reply_container.markdown(reply.replace("\n", " "))

            # 🌍 Translate back if needed
            if detected_lang != 'en':
                reply = GoogleTranslator(source='en', target=detected_lang).translate(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
