import streamlit as st
from openai import OpenAI, OpenAIError  # ✅ latest SDK style

# Create OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.subheader("Ask your question below:")

question = st.text_input("❓ Ask a Bible question (Swali lako):")

if question:
    try:
        with st.spinner("Answering..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            st.success(response.choices[0].message.content)
    except OpenAIError:
        st.error("🚫 API Authentication failed. Please double-check your key.")
    except Exception as e:
        st.error(f"💥 Unexpected error:\n\n{str(e)}")

st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
