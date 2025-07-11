# 📦 MODULE: biblebot_ui.py
import streamlit as st
from openai import OpenAI
from langdetect import detect
from deep_translator import GoogleTranslator
import os
from datetime import datetime


def biblebot_ui():
    # ✅ Setup OpenAI Client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment.")
        return

    client = OpenAI(api_key=api_key)

    # 🌐 Language switcher
    st.session_state.lang = st.selectbox("🌍 Select language", ["en", "sw", "fr", "de", "es"], index=0)

    # ✅ Title
    st.subheader("📖 BibleBot (Multilingual)")

    # ✅ Clear Chat Option
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 📥 Chat Input Field
    user_input = st.chat_input("Type your question here:")

    # 📝 Handle typed input
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

    # 📱 Mobile Layout Tweaks (auto handled by Streamlit, but we can still add polish)
    st.markdown("""
        <style>
        .stTextInput input, .stChatInput input {
            font-size: 1rem !important;
        }
        .stDownloadButton button {
            font-size: 0.9rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # © Credit - Always show
    st.markdown("---")
    st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")
