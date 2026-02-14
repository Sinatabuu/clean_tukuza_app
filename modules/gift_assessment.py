import streamlit as st
from langdetect import detect
from deep_translator import GoogleTranslator

from modules.db import (
    get_db_connection,
    insert_gift_assessment,
    fetch_latest_gift_assessment,
    delete_gift_assessment_for_user,
)

from modules.gifts_engine import QUESTIONS_EN, TIEBREAKER, score_gifts, apply_tiebreak


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

    
    result = fetch_latest_gift_assessment(current_user_id)
    if result:
        r = result.get("results", {}) or {}
        top3 = r.get("top3", []) or []

        st.markdown("### 💡 Your Last Spiritual Gifts Result")
        st.info(
            f"- 🧠 Primary Gift: **{r.get('primary_gift', 'N/A')}**\n"
            f"- 🌟 Secondary Gift: **{r.get('secondary_gift', 'N/A')}**\n"
            f"- 🎯 Confidence Margin: **{round(float(r.get('margin', 0.0)), 3)}**"
    )

    if top3:
        st.markdown("#### Top 3 Gifts")
        for i, item in enumerate(top3, 1):
            st.markdown(f"- {i}. **{item.get('gift')}** (score: {round(float(item.get('score', 0.0)), 3)})")

    col1, col2 = st.columns(2)

    with col1:
        user_name_for_report = st.session_state.get("user_name", "N/A")
        report_content = f"""Tukuza Yesu Spiritual Gifts Report

User Name: {user_name_for_report}

Primary Gift: {r.get('primary_gift', 'N/A')}
Secondary Gift: {r.get('secondary_gift', 'N/A')}

Top 3:
"""
        for i, item in enumerate(top3, 1):
            report_content += f"\n{i}. {item.get('gift')} (score: {round(float(item.get('score', 0.0)), 3)})"

        report_content += """

Note:
This assessment identifies edification gifts for serving and building up the body of Christ.
It does not determine fivefold office calling.

Built with faith by Sammy Karuri | Tukuza Yesu AI Toolkit
"""

        st.download_button(
            "⬇️ Download Gifts Report",
            report_content,
            file_name=f"tukuza_gifts_report_{user_name_for_report.replace(' ', '_').lower()}.txt",
            mime="text/plain",
            key=f"download_gifts_report_{current_user_id}",
        )

    with col2:
        if st.button("🧹 Clear Previous Gifts Result", key=f"clear_gifts_{current_user_id}"):
            delete_gift_assessment_for_user(current_user_id)
            st.success("Cleared.")
            st.rerun()
st.subheader("Take a New Spiritual Gifts Assessment")

sample_input = st.text_input(
    "🌐 Type anything in your language to personalize the experience:",
    key="sample_lang_input_assessment",
)

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

scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
if user_lang != "en":
    try:
        scale_instruction = GoogleTranslator(source="en", target=user_lang).translate(scale_instruction)
    except Exception:
        pass

st.caption(scale_instruction)
st.caption("This section measures edification gifts (not fivefold office calling).")

# Translate questions if needed (optional; you can cache later for speed)
questions = QUESTIONS_EN
if user_lang != "en":
    try:
        tr = GoogleTranslator(source="en", target=user_lang)
        questions = [tr.translate(q) for q in QUESTIONS_EN]
    except Exception:
        questions = QUESTIONS_EN

with st.form("gifts_core_form"):
    responses = [
        st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_core_{i}_{current_user_id}")
        for i, q in enumerate(questions)
    ]
    submitted = st.form_submit_button("🎯 Calculate My Gifts")

if submitted:
    base = score_gifts(responses)

    final = base
    used_tiebreak = False

    if base.needs_tiebreak:
        st.warning("Your top two gifts are very close. Answer 6 quick tie-breaker questions for accuracy.")

        # translate tie-breaker too
        t_primary = TIEBREAKER[base.primary]
        t_secondary = TIEBREAKER[base.secondary]
        if user_lang != "en":
            try:
                tr = GoogleTranslator(source="en", target=user_lang)
                t_primary = [tr.translate(q) for q in t_primary]
                t_secondary = [tr.translate(q) for q in t_secondary]
            except Exception:
                pass

        with st.form("gifts_tiebreak_form"):
            st.markdown(f"### Tie-breaker: {base.primary}")
            tie_primary = [
                st.slider(q, 1, 5, 3, key=f"tie_{base.primary}_{j}_{current_user_id}")
                for j, q in enumerate(t_primary)
            ]

            st.markdown(f"### Tie-breaker: {base.secondary}")
            tie_secondary = [
                st.slider(q, 1, 5, 3, key=f"tie_{base.secondary}_{j}_{current_user_id}")
                for j, q in enumerate(t_secondary)
            ]

            tie_submit = st.form_submit_button("✅ Finalize Result")

        if tie_submit:
            final = apply_tiebreak(base, tie_primary, tie_secondary)
            used_tiebreak = True
        else:
            st.stop()

    results = {
        "engine": "gifts_v2_deterministic",
        "primary_gift": final.primary,
        "secondary_gift": final.secondary,
        "top3": [{"gift": g, "score": float(s)} for g, s in final.top3],
        "scores": {k: float(v) for k, v in final.scores.items()},
        "margin": float(final.margin),
        "used_tiebreak": used_tiebreak,
    }

    insert_gift_assessment(
        session_id=str(current_user_id),
        language=str(user_lang),
        answers={"responses": responses},
        results=results,
    )

    st.success("✅ Saved! Your results will appear above.")
    st.rerun()
