# 📦 MODULE: discipleship_tracker_ui.py
import streamlit as st
import uuid
import json
import os
from datetime import datetime
from deep_translator import GoogleTranslator
from langdetect import detect


def discipleship_tracker_ui():
    st.subheader("🌱 Discipleship Growth Tracker")

    # 👤 Generate or retrieve user profile ID
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]

    user_id = st.session_state.user_id
    st.caption(f"User ID: {user_id}")

    # 🌍 Language Detection
    intro_text = st.text_input("✝️ Type something in your language (e.g. 'Yesu ni Bwana'):")
    user_lang = "en"
    if intro_text:
        try:
            user_lang = detect(intro_text)
        except:
            user_lang = "en"

    # 🧭 Discipleship Stages
    stages = ["New Believer", "Growing Disciple", "Faith Leader"]
    stage_translated = stages
    if user_lang != "en":
        stage_translated = [GoogleTranslator(source="en", target=user_lang).translate(s) for s in stages]

    selected_stage = st.selectbox("🌿 Select your current discipleship stage:", stage_translated)

    # 📋 Spiritual Habits Questions
    questions_en = [
        "How often do you spend time in prayer?",
        "How regularly do you read and reflect on the Bible?",
        "Do you participate in Christian fellowship or community?",
        "How often do you share your faith with others?",
        "How engaged are you in serving others or your church?"
    ]

    questions = questions_en
    if user_lang != "en":
        questions = [GoogleTranslator(source='en', target=user_lang).translate(q) for q in questions_en]

    st.markdown("---")
    st.caption("📊 Reflect on a scale from 1 (Never) to 5 (Always)")

    scores = []
    for i, q in enumerate(questions):
        score = st.slider(f"{i+1}. {q}", 1, 5, 3)
        scores.append(score)

    # 📝 Reflection
    reflection_label = "Write a short reflection about your spiritual growth this week."
    if user_lang != "en":
        reflection_label = GoogleTranslator(source='en', target=user_lang).translate(reflection_label)

    reflection = st.text_area(reflection_label)

    # 📤 Save & Download
    if st.button("💾 Save My Growth Report"):
        report = {
            "user_id": user_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "discipleship_stage": selected_stage,
            "scores": dict(zip(questions_en, scores)),
            "reflection": reflection
        }

        file_name = f"growth_report_{user_id}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)

        with open(file_name, "rb") as f:
            st.download_button("⬇️ Download My Report", f, file_name=file_name, mime="application/json")

    st.markdown("---")
    st.caption("📈 Track your growth consistently to strengthen your walk with Christ.")
