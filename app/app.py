import streamlit as st
import openai
import os
import joblib
import numpy as np

# ✅ FORCED GIT UPDATE — Multilingual version

# ---------------------------
# App Config
# ---------------------------
st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="centered")

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.sidebar.title("Tukuza Yesu")
tool = st.sidebar.radio("🛠 Choose a Tool:", [
    "📖 BibleBot", 
    "🔖 Verse Classifier", 
    "🌅 Daily Verse", 
    "🧪 Spiritual Gifts Assessment"
])

st.title("Tukuza Yesu AI Toolkit")

# ---------------------------
# 1. BibleBot
# ---------------------------
if tool == "📖 BibleBot":
    
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY"))

    st.subheader("Ask the BibleBot 📜")
    st.caption("🙋 Ask anything related to the Bible or Christian life.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    question = st.chat_input("🖋️ Ask your Bible question...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        try:
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

# ---------------------------
# 2. Verse Classifier
# ---------------------------
elif tool == "🔖 Verse Classifier":
    st.subheader("Classify a Bible Verse")

    model_path = os.path.join("models", "model.pkl")
    vectorizer_path = os.path.join("models", "vectorizer.pkl")

    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    st.write("🧠 Model can detect these topics:", model.classes_)

    verse = st.text_area("Paste a Bible verse here:")
    if st.button("Classify"):
        if verse.strip() == "":
            st.warning("Please enter a verse.")
        else:
            X = vectorizer.transform([verse])
            prediction = model.predict(X)[0]
            st.success(f"🧠 Detected Topic: **{prediction}**")

# ---------------------------
# 3. Daily Verse
# ---------------------------
elif tool == "🌅 Daily Verse":
    st.subheader("🌞 Your Daily Verse")
    verse = "“This is the day that the Lord has made; let us rejoice and be glad in it.” – Psalm 118:24"
    st.success(verse)

# ---------------------------
# 4. Spiritual Gifts Assessment
# ---------------------------
from deep_translator import GoogleTranslator
from langdetect import detect

if tool == "🧪 Spiritual Gifts Assessment":

# Load model
    model_path = os.path.join("models", "gift_model.pkl")
    model = joblib.load(model_path)

    st.subheader("🧪 Spiritual Gifts Assessment")

    sample_input = st.text_input("🌐 Type anything in your language to personalize the experience (e.g. 'Yesu ni Bwana'):")

        if sample_input:
            try:
                user_lang = detect(sample_input)
            except:
                user_lang = "en"
        else:
            user_lang = "en"
        
        
        # Original questions in English
        questions_en = [
            "I enjoy explaining Bible truths in a clear, structured way.",
            "I naturally take the lead when organizing ministry activities.",
            "I feel driven to share the gospel with strangers.",
            "I often sense spiritual warnings or encouragements for others.",
            "I easily feel compassion for people who are suffering.",
            "I enjoy giving resources to help others, even when it costs me.",
            "I’m happiest when working behind the scenes to help others.",
            "People often ask for my advice in complex spiritual matters.",
            "I enjoy studying and understanding deep biblical concepts.",
            "I trust God even in situations where others worry.",
            "I can often sense when something is spiritually wrong or deceptive.",
            "I enjoy hosting people and making them feel welcome.",
            "I often feel led to pray for others, even for long periods.",
            "I’m concerned about the spiritual growth of those around me.",
            "I naturally uplift others who are discouraged or unsure.",
            "I’ve prayed for people and seen them emotionally or physically healed.",
            "I enjoy pioneering new ministries or reaching unreached people.",
            "I enjoy managing projects and keeping people on track.",
            "I have spoken in a spiritual language not understood by others.",
            "I can understand and explain messages spoken in tongues.",
            "I stand firm in my faith even in hostile or public settings.",
            "I prepare lessons that help people grow in their faith.",
            "I look for ways to bring spiritual truth into everyday conversations.",
            "I cry or feel deeply moved when others are in pain.",
            "I often give above my tithe when I see a need.",
            "I influence others toward a vision in ministry.",
            "I can distinguish between truth and error without visible signs.",
            "I’ve had dreams, impressions, or messages that turned out accurate.",
            "I take personal responsibility for the spiritual welfare of others.",
            "I write or speak encouraging words that impact others deeply."
        ]
        
        gift_to_fivefold = {
            "Teaching": "Teacher",
            "Prophecy": "Prophet",
            "Evangelism": "Evangelist",
            "Service": "Pastor",
            "Giving": "Pastor",
            "Mercy": "Pastor",
            "Leadership": "Apostle"
        }
        
        
        # Detect language from first user interaction
        
        if sample_input:
            try:
                user_lang = detect(sample_input)
            except:
                user_lang = "en"
        else:
            user_lang = "en"
        
        # Translate questions
        if user_lang != "en":
            questions = [GoogleTranslator(source="en", target=user_lang).translate(q) for q in questions_en]
        else:
            questions = questions_en
        
        # UI
        st.subheader("🧪 Spiritual Gifts Assessment")
        st.caption("Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree).")
        
        with st.form("gift_assessment_form"):
            responses = []
            for i, q in enumerate(questions):
                score = st.slider(f"{i+1}. {q}", 1, 5, 3)
                responses.append(score)
        
            submitted = st.form_submit_button("🎯 Discover My Spiritual Gift")
        
        if submitted:
            try:
                input_data = np.array(responses).reshape(1, -1)
                prediction = model.predict(input_data)[0]
                role = gift_to_fivefold.get(prediction, "Undetermined")
        
                result_msg = f"🧠 Your dominant spiritual gift is: {prediction}"
                role_msg = f"👑 This aligns with the Fivefold Ministry Role: {role}"
                verse_msg = "✝️ 'So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers...' – Ephesians 4:11"
        
                # Translate if needed
                if user_lang != "en":
                    result_msg = GoogleTranslator(source="en", target=user_lang).translate(result_msg)
                    role_msg = GoogleTranslator(source="en", target=user_lang).translate(role_msg)
                    verse_msg = GoogleTranslator(source="en", target=user_lang).translate(verse_msg)
        
                st.success(result_msg)
                st.info(role_msg)
                st.markdown(verse_msg)
        
                # Downloadable summary
                summary_text = f"""
🎁 Spiritual Gifts Assessment

Dominant Gift: {prediction}
Fivefold Role: {role}
"""

        if user_lang != "en":
            summary_text = GoogleTranslator(source="en", target=user_lang).translate(summary_text)

        st.download_button(
            label="📥 Download My Result",
            data=summary_text,
            file_name="gift_result.txt",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"⚠️ Error during prediction: {e}")
