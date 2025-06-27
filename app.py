import streamlit as st
import openai
from openai import OpenAIError

# Set the OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]
st.write("🔑 API key detected." if openai.api_key else "❌ No API key found.")

# Streamlit page setup
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.subheader("Ask your question below:")

# Input
question = st.text_input("❓ Ask a Bible question (Swali lako):")

# Handle question
if question:
    try:
        with st.spinner("Answering..."):
            response = openai.ChatCompletion.create(  # ✅ Works on all OpenAI 1.x versions
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            st.success(response.choices[0].message["content"])
    except OpenAIError:
        st.error("🚫 API error — check your key or usage limits.")
    except Exception as e:
        st.error(f"💥 Unexpected error:\n\n{str(e)}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
