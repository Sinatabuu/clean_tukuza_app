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
from langdetect import detect
from deep_translator import GoogleTranslator

# 🌍 Translation Functions
def translate_user_input(text, target_lang="en"):
    detected_lang = detect(text)
    if detected_lang != 'en':
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated, detected_lang
    return text, detected_lang

def translate_bot_response(text, target_lang):
    from deep_translator import GoogleTranslator
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

# 🔐 Session-based user profile
if "user_profile" not in st.session_state:
    st.subheader("👤 Create Your Discipleship Profile")

    name = st.text_input("Your Name")
    stage = st.selectbox("Your Faith Stage", [
        "New Believer", "Growing Disciple", "Ministry Ready", "Faith Leader"
    ])

    if st.button("✅ Save Profile"):
        st.session_state.user_profile = {
            "name": name,
            "stage": stage,
            "history": []
        }
        st.success("Profile created for this session!")

elif "user_profile" in st.session_state:
    profile = st.session_state.user_profile
    st.success(f"Welcome back, {profile['name']} – {profile['stage']}")
    st.json(profile)

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.markdown("### ✝️ Tukuza Yesu Toolkit")
tool = st.selectbox("🛠️ Select a Tool", [
    "📖 BibleBot",
    "🔖 Verse Classifier",
    "🌅 Daily Verse",
    "🧪 Spiritual Gifts Assessment"
], index=0)  # Default to BibleBot

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
    if "user_profile" not in st.session_state:
        st.warning("⚠️ Please create your discipleship profile before continuing.")
        st.stop()

    model_path = os.path.join("models", "gift_model.pkl")
    model = joblib.load(model_path)

       # ✅ Reset button (only shows if previous result exists)
    if "user_profile" in st.session_state and "gift_results" in st.session_state.user_profile:
        if st.button("🧹 Clear Previous Gift Assessment"):
            st.session_state.user_profile.pop("gift_results", None)
            st.experimental_rerun()  # Rerun immediately before trying to use gift_results

    # ✅ Now it's safe to read from gift_results
    if "user_profile" in st.session_state and "gift_results" in st.session_state.user_profile:
        gr = st.session_state.user_profile["gift_results"]

        st.markdown("### 💡 Your Last Spiritual Gift Assessment")
        st.info(f"""
        - 🧠 Primary Gift: **{gr.get('primary', 'N/A')}** ({gr.get('primary_role', 'N/A')})  
        - 🌟 Secondary Gift: **{gr.get('secondary', 'N/A')}** ({gr.get('secondary_role', 'N/A')})
        """)

        st.markdown("### 🚀 Suggested Ministry Pathways")
        for i, role in enumerate(gr.get("ministries", []), 1):
            st.markdown(f"- {i}. **{role}**")

    # ✅ Always show the form heading
    st.subheader("🧪 Spiritual Gifts Assessment")


    sample_input = st.text_input("🌐 Type anything in your language to personalize the experience:")

    SUPPORTED_LANG_CODES = list(GoogleTranslator().get_supported_languages(as_dict=True).values())

    user_lang = "en"
    if sample_input.strip():
        try:
            detected = detect(sample_input)
            if detected in SUPPORTED_LANG_CODES:
                user_lang = detected
            else:
                st.warning(f"⚠️ Language '{detected}' not supported. Defaulting to English.")
        except:
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

    # Translate questions if needed
    questions = questions_en
    if user_lang != "en":
        try:
            questions = [GoogleTranslator(source="en", target=user_lang).translate(q) for q in questions_en]
        except:
            st.warning("⚠️ Translation failed. Using English.")

    # Instruction
    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        try:
            scale_instruction = GoogleTranslator(source='en', target=user_lang).translate(scale_instruction)
        except:
            pass
    st.caption(scale_instruction)

    # Form
    with st.form("gift_assessment_form", clear_on_submit=True):
        responses = [st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_slider_{i}") for i, q in enumerate(questions)]

        submit_text = "🎯 Discover My Spiritual Gift"
        if user_lang != "en":
            try:
                submit_text = GoogleTranslator(source="en", target=user_lang).translate(submit_text)
            except:
                pass

        submitted = st.form_submit_button(submit_text)

    if submitted:
        try:
            input_data = np.array(responses).reshape(1, -1)
            probs = model.predict_proba(input_data)[0]
            top2 = np.argsort(probs)[-2:][::-1]

            primary = model.classes_[top2[0]]
            secondary = model.classes_[top2[1]]

            primary_role = gift_to_fivefold.get(primary, "Undetermined")
            secondary_role = gift_to_fivefold.get(secondary, "Undetermined")

            gift_ministry_map = {
                "Teaching": ["Bible Study Leader", "Discipleship Coach", "Apologist"],
                "Prophecy": ["Intercessor", "Prophetic Mentor", "Watchman"],
                "Evangelism": ["Street Evangelist", "Mission Worker", "Church Planter"],
                "Service": ["Church Operations", "Setup Crew", "Admin Support"],
                "Mercy": ["Counselor", "Hospital Chaplain", "Comfort Ministry"],
                "Giving": ["Donor Relations", "Fundraising Coordinator", "Business-as-Mission"],
                "Leadership": ["Ministry Director", "Visionary Leader", "Team Builder"]
            }

            def recommend_ministries(primary, secondary, gift_map):
                return list(set(gift_map.get(primary, []) + gift_map.get(secondary, [])))[:3]

            ministry_suggestions = recommend_ministries(primary, secondary, gift_ministry_map)

            # Save to session
            st.session_state.user_profile["gift_results"] = {
                "primary": primary,
                "secondary": secondary,
                "primary_role": primary_role,
                "secondary_role": secondary_role,
                "ministries": ministry_suggestions
            }

            # Display
            result_msg = f"🧠 Primary Spiritual Gift: {primary}"
            secondary_msg = f"🌟 Secondary Spiritual Gift: {secondary}"
            role_msg = f"👑 Fivefold Roles: Primary – {primary_role} | Secondary – {secondary_role}"
            verse_msg = "✝️ 'So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers...' – Ephesians 4:11"

            if user_lang != "en":
                try:
                    result_msg = GoogleTranslator(source="en", target=user_lang).translate(result_msg)
                    secondary_msg = GoogleTranslator(source="en", target=user_lang).translate(secondary_msg)
                    role_msg = GoogleTranslator(source="en", target=user_lang).translate(role_msg)
                    verse_msg = GoogleTranslator(source="en", target=user_lang).translate(verse_msg)
                except:
                    pass

            st.success(result_msg)
            st.info(secondary_msg)
            st.markdown(role_msg)
            st.markdown(verse_msg)

            st.markdown("### 🚀 Suggested Ministry Pathways")
            for i, role in enumerate(ministry_suggestions, 1):
                st.markdown(f"- {i}. **{role}**")

        except Exception as e:
            st.error(f"⚠️ Error during prediction: {e}")
