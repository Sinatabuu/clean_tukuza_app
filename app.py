import streamlit as st
import openai

# ✅ Correct way to use API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🔧 Optional debug check
st.write("🔑 API key detected." if openai.api_key else "❌ No API key found.")

st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")
st.title("📖 Tukuza Yesu BibleBot")
st.subheader("Ask your question below:")

# Get user input
question = st.text_input("❓ Ask a Bible question (Swali lako):")

if question:
    try:
        with st.spinner("Answering..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            # ✅ This works with all OpenAI versions before and after 1.0
            st.success(response.choices[0].message["content"])
    except openai.error.AuthenticationError:
        st.error("🚫 API Authentication failed. Check your OpenAI key.")
    except Exception as e:
        st.error(f"💥 Unexpected error:\n\n{str(e)}")

# Footer
st.markdown(
    "<hr><div style='text-align: center; font-size: 12px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
