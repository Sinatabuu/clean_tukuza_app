import streamlit as st
import openai

# ✅ Configure the Streamlit page
st.set_page_config(page_title="Tukuza Yesu BibleBot", page_icon="📖")

# ✅ Title and credit
st.title("📖 Tukuza Yesu BibleBot")
st.caption("✝️ Created by Sammy Maigwa Karuri — Powered by GPT-3.5")

# ✅ Set your OpenAI API key here
openai.api_key = st.secrets["OPENAI_API_KEY"]
  # Replace with your real key

# ✅ Input box
question = st.text_input(
    "❓ Ask a Bible question (Swali lako):",
    
)

# ✅ Response logic
if question:
    with st.spinner("🔄 Thinking..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Bible-based assistant."},
                    {"role": "user", "content": question}
                ]
            )
            st.success(response.choices[0].message["content"])
        except openai.AuthenticationError:
            st.error("🚫 API Authentication failed. Double-check your key.")
        except Exception as e:
            st.error(f"💥 Unexpected error: {str(e)}")


# ✅ Footer with your credit
st.markdown(
    "<hr><div style='text-align: center; font-size: 14px; color: gray;'>"
    "✝️ Created by <strong>Sammy Maigwa Karuri</strong> — Tukuza Yesu AI Toolkit"
    "</div>",
    unsafe_allow_html=True
)
