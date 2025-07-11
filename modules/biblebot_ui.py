# 📦 MODULE: biblebot_ui.py
import streamlit as st
from openai import OpenAI
from langdetect import detect
from deep_translator import GoogleTranslator
import speech_recognition as sr
import os

def biblebot_ui():
    # ✅ Setup OpenAI Client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment.")
        return

    client = OpenAI(api_key=api_key)

    # ✅ Title
    st.subheader("📖 BibleBot (Multilingual)")

    # ✅ Clear Chat Option
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 🎤 Mic Button beside Chat Input
    mic_clicked = st.button("🎤", key="biblebot_mic")

    # 🖊️ Chat input field with enter/send icon
    user_input = st.chat_input("Type or speak your question:")

    # 🎤 Handle voice input
    if mic_clicked:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                voice_text = recognizer.recognize_google(audio)
                user_input = voice_text
            except sr.UnknownValueError:
                st.warning("⚠️ Could not understand.")
                return
            except Exception as e:
                st.error(f"🎤 Error: {e}")
                return

    # 📝 Handle typed or voice input
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Detect and translate
        detected_lang = detect(user_input)
        original_lang = detected_lang
        input_en = GoogleTranslator(source='auto', target='en').translate(user_input) if detected_lang != 'en' else user_input

        # Send to OpenAI
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": input_en}],
                stream=True,
            )

            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                reply_container = st.empty()
                reply = ""
                for chunk in stream:
                    part = chunk.choices[0].delta.content or ""
                    reply += part

            # Translate after stream ends
            if original_lang != 'en':
                reply = GoogleTranslator(source='en', target=original_lang).translate(reply)

            reply_container.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

    # Display last chat only
    if st.session_state.messages:
        last_user = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
        last_bot = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), "")
        if last_user and last_bot:
            st.markdown("### 💬 Chat Summary")
            st.markdown(f"**👋 You:** {last_user}")
            st.markdown(f"**🤖 BibleBot:** {last_bot}")

    # © Credit
    st.markdown("---")
    st.caption("Built with faith by Sammy Karuri ✡ | Tukuza Yesu AI Toolkit 🌐")
