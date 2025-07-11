# 📦 MODULE: biblebot_ui.py
import streamlit as st
from openai import OpenAI
from langdetect import detect
from deep_translator import GoogleTranslator
import speech_recognition as sr
import os
import streamlit.components.v1 as components
from datetime import datetime


def biblebot_ui():
    # ✅ Setup OpenAI Client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment.")
        return

    client = OpenAI(api_key=api_key)

    # ✅ Detect Mobile (Responsive)
    if "is_mobile" not in st.session_state:
        components.html(
            """
            <script>
                const isMobile = window.innerWidth < 768;
                const streamlitDoc = window.parent.document;
                streamlitDoc.body.setAttribute('data-mobile', isMobile);
                window.parent.postMessage({ type: 'streamlit:setComponentValue', value: isMobile }, '*');
            </script>
            """,
            height=0,
        )
        st.session_state.is_mobile = False  # default fallback

    # 🌐 Language switcher
    st.session_state.lang = st.selectbox("🌍 Select language", ["en", "sw", "fr", "de", "es"], index=0)

    # ✅ Title
    st.subheader("📖 BibleBot (Multilingual)")

    # ✅ Clear Chat Option
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 📥 Chat Input Field + Mic Button (desktop only)
    col1, col2 = st.columns([9, 1])
    with col1:
        user_input = st.chat_input("Type or speak your question:")
    with col2:
        mic_clicked = False
        if not st.session_state.get("is_mobile", False):
            mic_clicked = st.button("🎤", key="biblebot_mic")

    # 🎤 Handle voice input (desktop only)
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

        # Translate if not in English
        selected_lang = st.session_state.lang
        input_en = GoogleTranslator(source='auto', target='en').translate(user_input) if selected_lang != 'en' else user_input

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
            if selected_lang != 'en':
                reply = GoogleTranslator(source='en', target=selected_lang).translate(reply)

            reply_container.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            # 💾 Save chat (simple local file)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = f"chat_{timestamp}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                for msg in st.session_state.messages:
                    role = msg['role']
                    content = msg['content']
                    f.write(f"{role.upper()}:\n{content}\n\n")

            with open(file_path, "rb") as f:
                st.download_button("📥 Download Chat", f, file_name=file_path, mime="text/plain")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

    # Display last chat only (optional)
    if st.session_state.messages:
        last_user = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
        last_bot = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), "")
        if last_user and last_bot:
            st.markdown("### 💬 Chat Summary")
            st.markdown(f"**👋 You:** {last_user}")
            st.markdown(f"**🤖 BibleBot:** {last_bot}")

    # 📱 Mobile Layout Tweaks
    if st.session_state.get("is_mobile", False):
        st.markdown("<style>.stButton, .stTextInput, .stDownloadButton { font-size: 90% !important; }</style>", unsafe_allow_html=True)

    # © Credit - Always show
    st.markdown("---")
    st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")
