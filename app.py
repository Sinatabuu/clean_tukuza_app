import streamlit as st
import openai

# ✅ Set your API key from Streamlit Cloud secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.subheader("Ask your question below:")

question = st.text_input("❓ Ask a Bible question (Swali lako):")

if question:
    try:
        with st.spinner("Answering..."):
            # ✅ Correct API call for OpenAI v1.x
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            # ✅ Proper way to access content in v1.x
            st.success(response.choices[0].message.content)
    except Exception as e:
        st.error(f"💥 Unexpected error:\n\n{str(e)}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
