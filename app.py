import streamlit as st
import openai
import os

# ✅ New openai client for version >=1.6
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Streamlit Setup ---
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.caption("🖊️ Ask your Bible question below")

# --- Chat memory ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- User input ---
question = st.chat_input("Type your Bible question here...")

# --- Chat logic ---
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    try:
        # ✅ Correct modern API call
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

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
