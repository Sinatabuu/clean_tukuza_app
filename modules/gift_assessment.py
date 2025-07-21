import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import joblib
from langdetect import detect
from deep_translator import GoogleTranslator
from modules.db import get_db_connection, insert_gift_assessment, fetch_latest_gift_assessment, delete_gift_assessment_for_user

def gift_assessment_ui():
    """
    Spiritual Gifts Assessment UI
    """
    st.subheader("🧪 Spiritual Gifts Assessment")

    # Ensure user is authenticated
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
        return

    current_user_id = st.session_state.user_id

    # --- Load models ---
    model_path = os.path.join("models", "gift_model.pkl")
    if not os.path.exists(model_path):
        st.error("Spiritual gifts model file not found. Please ensure 'gift_model.pkl' is in the 'models' directory.")
        return
    model = joblib.load(model_path)

    # --- Display Previous Assessment Results ---
    with get_db_connection() as conn:
        result = fetch_latest_gift_assessment(current_user_id)
        if result:
            gr = {
                "primary": result[0],
                "secondary": result[1],
                "primary_role": result[2],
                "secondary_role": result[3],
                "ministries": json.loads(result[4]) if result[4] else []
            }

            st.markdown("### 💡 Your Last Spiritual Gift Assessment")
            st.info(f"""
            - 🧠 Primary Gift: **{gr.get('primary', 'N/A')}** ({gr.get('primary_role', 'N/A')})
            - 🌟 Secondary Gift: **{gr.get('secondary', 'N/A')}** ({gr.get('secondary_role', 'N/A')})
            """)
            st.markdown("### 🚀 Suggested Ministry Pathways")
            for greater, role in enumerate(gr.get("ministries", []), 1):
                st.markdown(f"- {greater}. **{role}**")

            col_buttons_1, col_buttons_2 = st.columns(2)
            with col_buttons_1:
                user_name_for_report = st.session_state.get('user_name', 'N/A')
                # Fetch stage from database if not in session_state
                cursor = conn.cursor()
                cursor.execute("SELECT stage FROM user_profiles WHERE id = %s", (current_user_id,))
                user_profile_row = cursor.fetchone()
                stage = user_profile_row[0] if user_profile_row else 'N/A'

                report_content = f"""
Tukuza Yesu Spiritual Gifts Assessment Report

User Name: {user_name_for_report}
Faith Stage: {stage}

---

Your Spiritual Gift Assessment Results:

🧠 Primary Spiritual Gift: {gr.get('primary', 'N/A')} ({gr.get('primary_role', 'N/A')})
🌟 Secondary Spiritual Gift: {gr.get('secondary', 'N/A')} ({gr.get('secondary_role', 'N/A')})

---

🚀 Suggested Ministry Pathways:
"""
                for greater, role in enumerate(gr.get("ministries", []), 1):
                    report_content += f"- {greater}. {role}\n"

                report_content += """
---
"So Christ himself gave the apostles, the prophets, the evangelists, the pastors and teachers..." – Ephesians 4:11

Built with faith by Sammy Karuri ✡ | Tukuza Yesu AI Toolkit 🌐
"""
                st.download_button(
                    label="⬇️ Download Your Gift Report",
                    data=report_content,
                    file_name=f"tukuza_spiritual_gifts_report_{user_name_for_report.replace(' ', '_').lower()}.txt",
                    mime="text/plain",
                    key="download_gift_report_button"
                )
            with col_buttons_2:
                if st.button("🧹 Clear Previous Gift Assessment", key="clear_gift_assessment_button"):
                    delete_gift_assessment_for_user(current_user_id)
                    st.rerun()

    # --- New Assessment Form ---
    st.subheader("Take a New Spiritual Gifts Assessment")

    # Language detection for questions
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
        except Exception as e:
            st.warning(f"⚠️ Could not detect language: {str(e)}. Defaulting to English.")

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
        except Exception as e:
            st.warning(f"⚠️ Translation of questions failed: {str(e)}. Using English.")

    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        try:
            scale_instruction = GoogleTranslator(source='en', target=user_lang).translate(scale_instruction)
        except Exception as e:
            st.warning(f"⚠️ Translation failed: {str(e)}. Using English.")

    st.caption(scale_instruction)

    with st.form("gift_assessment_form", clear_on_submit=True):
        responses = [st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_slider_{i}") for i, q in enumerate(questions)]

        submit_text = "🎯 Discover My Spiritual Gift"
        if user_lang != "en":
            try:
                submit_text = GoogleTranslator(source="en", target=user_lang).translate(submit_text)
            except Exception as e:
                st.warning(f"⚠️ Translation failed: {str(e)}. Using English.")

        submitted = st.form_submit_button(submit_text)

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
                    "Giving": ["Donor Relations", "Fundraising Coordinator", "Business-as-Mission"],
                    "Mercy": ["Counselor", "Hospital Chaplain", "Comfort Ministry"],
                    "Leadership": ["Ministry Director", "Visionary Leader", "Team Builder"]
                }

                def recommend_ministries(primary, secondary, gift_map):
                    return list(set(gift_map.get(primary, []) + gift_map.get(secondary, [])))[:3]

                ministry_suggestions = recommend_ministries(primary, secondary, gift_ministry_map)

                gift_data = {
                    "primary_gift": primary,
                    "secondary_gift": secondary,
                    "primary_role": primary_role,
                    "secondary_role": secondary_role,
                    "ministries": ministry_suggestions
                }

                if insert_gift_assessment(current_user_id, gift_data):
                    st.success("Your assessment has been saved!")
                    st.rerun()
                else:
                    st.error("Failed to save assessment. Please try again.")

            except Exception as e:
                st.error(f"⚠️ Error during prediction or saving: {str(e)}")