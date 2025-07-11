# 📦 MODULE: biblebot_ui.py
import streamlit as st
from openai import OpenAI
from langdetect import detect
from deep_translator import GoogleTranslator
import os

def biblebot_ui():
    # ✅ Setup OpenAI Client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment.")
        return

    client = OpenAI(api_key=api_key)

    # ✅ Title and model selector
    st.subheader("📖 BibleBot (Multilingual)")
    model_choice = st.selectbox("🤖 Choose Model", ["gpt-3.5-turbo", "gpt-4"])

    # ✅ Clear Chat Option
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 📥 Input only
    user_input = st.text_input("Type your Bible question:", key="biblebot_input")

    # 📝 Handle typed input
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Detect and translate
        detected_lang = detect(user_input)
        original_lang = detected_lang
        input_en = GoogleTranslator(source='auto', target='en').translate(user_input) if detected_lang != 'en' else user_input

        # Send to OpenAI
        try:
            stream = client.chat.completions.create(
                model=model_choice,
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
                    reply_container.markdown(reply)

            # 🌐 Translate if needed
            if original_lang != 'en':
                reply = GoogleTranslator(source='en', target=original_lang).translate(reply)
                reply_container.markdown(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
