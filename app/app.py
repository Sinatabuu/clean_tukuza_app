import streamlit as st
from openai import OpenAI
import os
import joblib
import numpy as np
import pandas as pd
from streamlit_webrtc import webrtc_streamer
import av
import queue
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
# Email Sending Function
# ---------------------------
def send_gift_report_email(recipient_email, gift_results, user_profile, user_lang="en"):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD") # This should be an App Password if using Gmail with 2FA

    if not sender_email or not sender_password:
        return "Email credentials not set up. Please configure SENDER_EMAIL and SENDER_PASSWORD environment variables."

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = recipient_email

    # Constructing the email body
    primary_gift = gift_results.get("primary", "N/A")
    secondary_gift = gift_results.get("secondary", "N/A")
    primary_role = gift_results.get("primary_role", "Undetermined")
    secondary_role = gift_results.get("secondary_role", "Undetermined")
    ministries = gift_results.get("ministries", [])
    user_name = user_profile.get("name", "Valued User")
    user_faith_stage = user_profile.get("stage", "Undetermined")

    ministry_list_html = "<ul>" + "".join([f"<li><b>{m}</b></li>" for m in ministries]) + "</ul>"
    ministry_list_plain = "- " + "\n- ".join(ministries) if ministries else "N/A"

    subject_en = "Your Tukuza Yesu Spiritual Gifts Assessment Report"
    text_content_en = f"""
Dear {user_name},

Thank you for completing your Spiritual Gifts Assessment with Tukuza Yesu AI Toolkit!

Here is a summary of your results:

- Primary Spiritual Gift: {primary_gift} ({primary_role})
- Secondary Spiritual Gift: {secondary_gift} ({secondary_role})

Suggested Ministry Pathways:
{ministry_list_plain}

"So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers..." – Ephesians 4:11

May God bless you as you use your gifts for His glory!

Sincerely,
The Tukuza Yesu Team
"""

    html_content_en = f"""
<html>
    <body>
        <p>Dear {user_name},</p>
        <p>Thank you for completing your Spiritual Gifts Assessment with <b>Tukuza Yesu AI Toolkit</b>!</p>
        <p>Here is a summary of your results:</p>
        <ul>
            <li>🧠 Primary Spiritual Gift: <b>{primary_gift}</b> ({primary_role})</li>
            <li>🌟 Secondary Spiritual Gift: <b>{secondary_gift}</b> ({secondary_role})</li>
        </ul>
        <h3>🚀 Suggested Ministry Pathways:</h3>
        {ministry_list_html}
        <p>✝️ <i>"So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers..." – Ephesians 4:11</i></p>
        <p>May God bless you as you use your gifts for His glory!</p>
        <p>Sincerely,<br>The Tukuza Yesu Team</p>
    </body>
</html>
"""
    # Translate if necessary
    subject = subject_en
    text_content = text_content_en
    html_content = html_content_en

    if user_lang != "en":
        try:
            subject = GoogleTranslator(source="en", target=user_lang).translate(subject_en)
            text_content = GoogleTranslator(source="en", target=user_lang).translate(text_content_en)
            html_content = GoogleTranslator(source="en", target=user_lang).translate(html_content_en)
        except Exception:
            # Fallback to English if translation fails
            pass

    message["Subject"] = subject
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")

    message.attach(part1)
    message.attach(part2)

    try:
        # For Gmail, use smtp.gmail.com and port 465 for SSL or 587 for TLS
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        return "Email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {e}"

# ---------------------------
# App Config
# ---------------------------
st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="wide")

# 🔐 Session-based user profile
if "user_profile" not in st.session_state:
    st.subheader("👤 Create Your Discipleship Profile")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", key="profile_name_input")
    with col2:
        stage = st.selectbox("Your Faith Stage", [
            "New Believer", "Growing Disciple", "Ministry Ready", "Faith Leader"
        ], key="profile_stage_select")

    if st.button("✅ Save Profile", key="save_profile_button"):
        st.session_state.user_profile = {
            "name": name,
            "stage": stage,
            "history": []
        }
        st.success("Profile created for this session!")
        st.rerun()

elif "user_profile" in st.session_state:
    profile = st.session_state.user_profile
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"Welcome back, {profile['name']} – {profile['stage']}")
    with col2:
        st.markdown("<div style='text-align:right'>🧭 Profile loaded</div>", unsafe_allow_html=True)

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.markdown("### ✝️ Tukuza Yesu Toolkit")
tool = st.selectbox("🛠️ Select a Tool", [
    "📖 BibleBot",
    "🔖 Verse Classifier",
    "🌅 Daily Verse",
    "🧪 Spiritual Gifts Assessment"
], index=0, key="tool_selector")

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

    model_path = os.path.join("models", "model.pkl")
    vectorizer_path = os.path.join("models", "vectorizer.pkl")

    if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
        st.error("Model files not found. Please ensure 'model.pkl' and 'vectorizer.pkl' are in the 'models' directory.")
        st.stop()

    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    st.write("🧠 Model can detect these topics:", model.classes_)

    verse = st.text_area("Paste a Bible verse here:", key="verse_classifier_input")
    if st.button("Classify", key="classify_button"):
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
    if not os.path.exists(model_path):
        st.error("Spiritual gifts model file not found. Please ensure 'gift_model.pkl' is in the 'models' directory.")
        st.stop()

    model = joblib.load(model_path)

    # Check if results exist and display them first, along with the clear button
    if "gift_results" in st.session_state.user_profile:
        gr = st.session_state.user_profile["gift_results"]
        st.markdown("### 💡 Your Last Spiritual Gift Assessment")
        st.info(f"""
        - 🧠 Primary Gift: **{gr.get('primary', 'N/A')}** ({gr.get('primary_role', 'N/A')})
        - 🌟 Secondary Gift: **{gr.get('secondary', 'N/A')}** ({gr.get('secondary_role', 'N/A')})
        """)
        st.markdown("### 🚀 Suggested Ministry Pathways")
        for i, role in enumerate(gr.get("ministries", []), 1):
            st.markdown(f"- {i}. **{role}**")

        if st.button("🧹 Clear Previous Gift Assessment", key="clear_gift_assessment_button"):
            st.session_state.user_profile.pop("gift_results", None)
            st.rerun()
        
        st.stop() # Stop execution here if results are already shown.

    # Display the assessment form if no gift_results exist
    st.subheader("🧪 Spiritual Gifts Assessment")

    sample_input = st.text_input("🌐 Type anything in your language to personalize the experience:", key="sample_lang_input_assessment")

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

    questions = questions_en
    if user_lang != "en":
        try:
            questions = [GoogleTranslator(source="en", target=user_lang).translate(q) for q in questions_en]
        except:
            st.warning("⚠️ Translation failed. Using English.")

    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        try:
            scale_instruction = GoogleTranslator(source='en', target=user_lang).translate(scale_instruction)
        except:
            pass
    st.caption(scale_instruction)

    with st.form("gift_assessment_form", clear_on_submit=True):
        user_email = st.text_input("Your Email for Report (Optional)", key="report_email_input") # Email input added
        responses = [st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_slider_{i}") for i, q in enumerate(questions)]

        submit_text = "🎯 Discover My Spiritual Gift"
        if user_lang != "en":
            try:
                submit_text = GoogleTranslator(source="en", target=user_lang).translate(submit_text)
            except:
                pass

        submitted = st.form_submit_button(submit_text)

        # Process submission directly within the form's context
        if submitted:
            try:
                input_data = pd.DataFrame([responses], columns=[f"Q{i+1}" for i in range(len(responses))])
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

                st.session_state.user_profile["gift_results"] = {
                    "primary": primary,
                    "secondary": secondary,
                    "primary_role": primary_role,
                    "secondary_role": secondary_role,
                    "ministries": ministry_suggestions
                }

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

                # Send email if an email address was provided
                if user_email:
                    with st.spinner("Sending email report..."):
                        email_status = send_gift_report_email(user_email, st.session_state.user_profile["gift_results"], st.session_state.user_profile, user_lang)
                        if "successfully" in email_status:
                            st.success(f"Email report: {email_status}")
                        else:
                            st.error(f"Email report failed: {email_status}")
                else:
                    st.info("No email provided. Report will not be emailed.")

                st.rerun() # Rerun to display the results and hide the form

            except Exception as e:
                st.error(f"⚠️ Error during prediction: {e}")

# ---------------------------
# © Credit - Always show
# ---------------------------
st.markdown("---")
st.caption("Built with faith by **Sammy Karuri ✡** | Tukuza Yesu AI Toolkit 🌐")