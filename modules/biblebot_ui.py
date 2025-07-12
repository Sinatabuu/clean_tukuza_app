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

    # ✅ Initialize chat history if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ✅ Clear Chat Option
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        # To ensure the clear takes effect immediately and redraws,
        # you might want to rerun the app, but typically Streamlit handles this.
        st.experimental_rerun() # Added for immediate clear effect

    # 📬 Chat Input Field
    user_input = st.chat_input("Type your question here:")

    # 📝 Handle typed input (only process and append, don't display yet)
    if user_input:
        # Append user message immediately
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Translate user input if not in English
        selected_lang = st.session_state.lang
        input_en = GoogleTranslator(source='auto', target='en').translate(user_input) if selected_lang != 'en' else user_input

        # Send to OpenAI
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": input_en}],
                stream=True,
            )

            full_english_reply = ""
            # Collect the full English response first
            for chunk in stream:
                full_english_reply += chunk.choices[0].delta.content or ""

            final_display_reply = full_english_reply

            # Translate after getting full response, if needed
            if selected_lang != 'en':
                final_display_reply = GoogleTranslator(source='en', target=selected_lang).translate(full_english_reply)
            
            # Append assistant message
            st.session_state.messages.append({"role": "assistant", "content": final_display_reply})

            # 📂 Save chat (simple local file)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = f"chat_{timestamp}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                for msg in st.session_state.messages:
                    role = msg['role']
                    content = msg['content']
                    f.write(f"{role.upper()}:\n{content}\n\n")

            # This download button will also trigger a rerun, which is fine
            with open(file_path, "rb") as f:
                st.download_button("📅 Download Chat", f, file_name=file_path, mime="text/plain")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
        
        # After processing, rerun to display updated messages properly
        st.experimental_rerun()


    # 🚀 Display all chat messages from history (this is the ONLY place messages should be displayed)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


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