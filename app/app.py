import streamlit as st
from openai import OpenAI
import os
import joblib
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av
import queue
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.biblebot_ui import biblebot_ui


# 🌍 Translation Functions
def translate_user_input(text, target_lang="en"):
    detected_lang = detect(text)
    if detected_lang != 'en':
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated, detected_lang
    return text, detected_lang

def translate_bot_response(text, target_lang):
    if target_lang != 'en':
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    return text

# 🎤 Voice Input Setup
audio_queue = queue.Queue()

class AudioProcessor:
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio_queue.put(frame.to_ndarray().flatten().astype("float32").tobytes())
        return frame


# ---------------------------
# App Config
# ---------------------------
st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="wide")



# ---------------------------
# Sidebar Navigation
# ---------------------------
st.sidebar.title("✝️ Tukuza Yesu Toolkit")
st.sidebar.markdown("**Empowering Faith with AI**")


tool = st.sidebar.radio("🛠️ Select a Tool", [
    "📖 BibleBot",
    "🔖 Verse Classifier",
    "🌅 Daily Verse",
    "🧪 Spiritual Gifts Assessment"
])


# Optional footer or version
st.sidebar.markdown("---")
st.sidebar.caption("🔄 v1.0 | Developed by Sammy Karuri")

#st.title("Tukuza Yesu AI Toolkit")

# ---------------------------
# 1. BibleBot
# ---------------------------
if tool == "📖 BibleBot":
    biblebot_ui()
    

# ---------------------------
# 2. Verse Classifier
# ---------------------------
elif tool == "🔖 Verse Classifier":
    st.subheader("Classify a Bible Verse")

    model_path = os.path.join("models", "model.pkl")  # ✅ correct model
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
elif tool == "🧪 Spiritual Gifts Assessment":
    from deep_translator import GoogleTranslator
    from langdetect import detect

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

    if user_lang != "en":
        questions = [GoogleTranslator(source="en", target=user_lang).translate(q) for q in questions_en]
    else:
        questions = questions_en

    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        scale_instruction = GoogleTranslator(source='en', target=user_lang).translate(scale_instruction)
    st.caption(scale_instruction)


    with st.form("gift_assessment_form"):
       responses = [st.slider(f"{i+1}. {q}", 1, 5, 3) for i, q in enumerate(questions)]

    submit_text = "🎯 Discover My Spiritual Gift"
    if user_lang != "en":
        submit_text = GoogleTranslator(source='en', target=user_lang).translate(submit_text)

    submitted = st.form_submit_button(submit_text)

    if submitted:
        try:
            input_data = np.array(responses).reshape(1, -1)
            prediction = model.predict(input_data)[0]
            role = gift_to_fivefold.get(prediction, "Undetermined")

            result_msg = f"🧠 Your dominant spiritual gift is: {prediction}"
            role_msg = f"👑 This aligns with the Fivefold Ministry Role: {role}"
            verse_msg = "✝️ 'So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers...' – Ephesians 4:11"

            if user_lang != "en":
                result_msg = GoogleTranslator(source="en", target=user_lang).translate(result_msg)
                role_msg = GoogleTranslator(source="en", target=user_lang).translate(role_msg)
                verse_msg = GoogleTranslator(source="en", target=user_lang).translate(verse_msg)

            st.success(result_msg)
            st.info(role_msg)
            st.markdown(verse_msg)

        except Exception as e:
            st.error(f"⚠️ Error during prediction: {e}")
