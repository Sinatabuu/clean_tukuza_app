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
    # Place language selector and title before displaying messages
    st.session_state.lang = st.selectbox("🌍 Select language", ["en", "sw", "fr", "de", "es"], index=0)
    st.subheader("📖 BibleBot (Multilingual)")

    # ✅ Initialize chat history if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ✅ Clear Chat Option
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.experimental_rerun() # Force rerun to clear display immediately

    # 🚀 Display all chat messages from history on app rerun
    # This loop is the ONLY place where messages should be displayed
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 📬 Accept user input
    # Use the walrus operator (:=) for concise input handling
    if prompt := st.chat_input("Type your question here:"):
        # Add user message to chat history FIRST
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Translate user input if not in English
        selected_lang = st.session_state.lang
        # Use 'prompt' directly here, as it holds the original user input
        input_en = GoogleTranslator(source='auto', target='en').translate(prompt) if selected_lang != 'en' else prompt

        # Generate assistant response
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": input_en}],
                stream=True,
            )

            full_english_reply = ""
            # Collect the full English response from the stream without displaying yet
            for chunk in stream:
                full_english_reply += chunk.choices[0].delta.content or ""

            final_display_reply = full_english_reply

            # Translate after getting full response, if needed
            if selected_lang != 'en':
                final_display_reply = GoogleTranslator(source='en', target=selected_lang).translate(full_english_reply)
            
            # Add assistant message to chat history
            st.session_state.messages.append({"role": "assistant", "content": final_display_reply})

            # 📂 Save chat (simple local file) - This part will also trigger a rerun
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = f"chat_{timestamp}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                for msg in st.session_state.messages:
                    role = msg['role']
                    content = msg['content']
                    f.write(f"{role.upper()}:\n{content}\n\n")

            with open(file_path, "rb") as f:
                st.download_button("📅 Download Chat", f, file_name=file_path, mime="text/plain")

            # Force a rerun to update the display with the new messages in the history loop
            st.experimental_rerun()

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
            # If an error occurs, still append to history so the error is not lost
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
            st.experimental_rerun()


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