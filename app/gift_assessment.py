import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import joblib
from langdetect import detect
from deep_translator import GoogleTranslator 

# Import your database connection function
from db import get_db_connection

def gift_assessment_ui():
    """
    Spiritual Gifts Assessment UI
    """
    st.subheader("🧪 Spiritual Gifts Assessment")

    # Ensure user is authenticated first
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
        # Instead of st.stop(), which halts the entire script, return
        # to allow other parts of app.py to render or redirect.
        return

    current_user_id = st.session_state.user_id

    # --- Load models ---
    # @st.cache_resource is typically used for heavy resource loading once.
    # If this model is relatively small, loading it inside the function is fine,
    # but for larger models, consider caching it at the app.py level and passing it.
    # For now, let's keep it here, assuming joblib.load is fast enough.
    model_path = os.path.join("models", "gift_model.pkl")
    if not os.path.exists(model_path):
        st.error("Spiritual gifts model file not found. Please ensure 'gift_model.pkl' is in the 'models' directory.")
        return # Use return instead of st.stop()
    model = joblib.load(model_path)


    # --- Display Previous Assessment Results ---
    # Get connection and cursor *just before* using them
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT primary_gift, secondary_gift, primary_role, secondary_role, ministries FROM gift_assessments WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (current_user_id,))
    db_gift_results = cursor.fetchone()

    if db_gift_results:
        # Reconstruct the dictionary from DB tuple
        gr = {
            "primary": db_gift_results["primary_gift"], # Access by column name if row_factory is set
            "secondary": db_gift_results["secondary_gift"],
            "primary_role": db_gift_results["primary_role"],
            "secondary_role": db_gift_results["secondary_role"],
            "ministries": json.loads(db_gift_results["ministries"]) if db_gift_results["ministries"] else []
        }

        st.markdown("### 💡 Your Last Spiritual Gift Assessment")
        st.info(f"""
        - 🧠 Primary Gift: **{gr.get('primary', 'N/A')}** ({gr.get('primary_role', 'N/A')})
        - 🌟 Secondary Gift: **{gr.get('secondary', 'N/A')}** ({gr.get('secondary_role', 'N/A')})
        """)
        st.markdown("### 🚀 Suggested Ministry Pathways")
        for i, role in enumerate(gr.get("ministries", []), 1):
            st.markdown(f"- {i}. **{role}**")

        col_buttons_1, col_buttons_2 = st.columns(2)
        with col_buttons_1:
            # Ensure user_name is available in session_state, as user_auth was
            # a previous session state key that might no longer exist.
            # Assuming st.session_state.user_name holds the current user's name.
            user_name_for_report = st.session_state.get('user_name', 'N/A')
            # Assuming user_profiles table has a 'stage' column for the user
            # You might need to fetch this if it's not in session_state
            # Example:
            # stage = "N/A"
            # cursor.execute("SELECT stage FROM user_profiles WHERE id = ?", (current_user_id,))
            # user_profile_row = cursor.fetchone()
            # if user_profile_row:
            #     stage = user_profile_row['stage']
            
            # Simplified for now, assuming stage might not be directly available in session_state
            # if not, user_auth.get('stage') was causing issues in app.py.
            report_content = f"""
Tukuza Yesu Spiritual Gifts Assessment Report

User Name: {user_name_for_report}
Faith Stage: {st.session_state.get('user_stage', 'N/A')}

---

Your Spiritual Gift Assessment Results:

🧠 Primary Spiritual Gift: {gr.get('primary', 'N/A')} ({gr.get('primary_role', 'N/A')})
🌟 Secondary Spiritual Gift: {gr.get('secondary', 'N/A')} ({gr.get('secondary_role', 'N/A')})

---

🚀 Suggested Ministry Pathways:
"""
            for i, role in enumerate(gr.get("ministries", []), 1):
                report_content += f"- {i}. {role}\n"

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
                # Get connection and cursor *just before* using them for delete
                conn_delete = get_db_connection()
                cursor_delete = conn_delete.cursor()
                cursor_delete.execute("DELETE FROM gift_assessments WHERE user_id = ?", (current_user_id,))
                conn_delete.commit()
                st.experimental_rerun() # Use experimental_rerun for broader compatibility


        # IMPORTANT: Do not st.stop() here. This would prevent the assessment form from ever appearing
        # if a previous assessment exists. Instead, just let the function flow through.
        # st.stop() # Removed this line

    # --- New Assessment Form ---
    st.subheader("Take a New Spiritual Gifts Assessment") # Changed title for clarity

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
        except Exception: # Catch broader exceptions for langdetect
            st.warning("⚠️ Could not detect language. Defaulting to English.")
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
        except Exception: # Catch broader exceptions for translation
            st.warning("⚠️ Translation of questions failed. Using English.")

    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        try:
            scale_instruction = GoogleTranslator(source='en', target=user_lang).translate(scale_instruction)
        except Exception: # Catch broader exceptions for translation
            pass # Keep default English

    st.caption(scale_instruction)

    with st.form("gift_assessment_form", clear_on_submit=True):
        responses = [st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_slider_{i}") for i, q in enumerate(questions)]

        submit_text = "🎯 Discover My Spiritual Gift"
        if user_lang != "en":
            try:
                submit_text = GoogleTranslator(source="en", target=user_lang).translate(submit_text)
            except Exception: # Catch broader exceptions for translation
                pass # Keep default English

        # Fix: The button label should be the string variable, not the variable name
        submitted = st.form_submit_button(submit_text) # Corrected this line

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

                # Get connection and cursor *just before* using them for insert
                conn_insert = get_db_connection()
                cursor_insert = conn_insert.cursor()

                cursor_insert.execute("""
                    INSERT INTO gift_assessments (user_id, primary_gift, secondary_gift, primary_role, secondary_role, ministries)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    current_user_id,
                    primary,
                    secondary,
                    primary_role,
                    secondary_role,
                    json.dumps(ministry_suggestions)
                ))
                conn_insert.commit()

                st.success("Your assessment has been saved!")
                st.experimental_rerun() # Use experimental_rerun for broader compatibility

            except Exception as e:
                st.error(f"⚠️ Error during prediction or saving: {e}")