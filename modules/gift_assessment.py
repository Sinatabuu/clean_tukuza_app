# modules/gift_assessment.py

import streamlit as st
from langdetect import detect
from deep_translator import GoogleTranslator

from modules.db import (
    insert_gift_assessment,
    fetch_latest_gift_assessment,
    delete_gift_assessment_for_user,
)

from modules.gifts_engine import QUESTIONS_EN, TIEBREAKER, score_gifts, apply_tiebreak
from modules.db import fetch_recent_gift_assessments

def _confidence_label(margin: float) -> str:
    if margin >= 0.35:
        return "High"
    if margin >= 0.20:
        return "Medium"
    return "Low"

def _detect_language(sample_text: str) -> str:
    """Return language code supported by GoogleTranslator; default to 'en'."""
    user_lang = "en"
    if not sample_text or not sample_text.strip():
        return user_lang

    try:
        supported = list(GoogleTranslator().get_supported_languages(as_dict=True).values())
        detected = detect(sample_text)
        if detected in supported:
            return detected
    except Exception:
        pass

    return "en"


def _translate_list(items, user_lang: str):
    """Translate a list of English strings to user_lang; fallback to English."""
    if user_lang == "en":
        return items
    try:
        tr = GoogleTranslator(source="en", target=user_lang)
        return [tr.translate(x) for x in items]
    except Exception:
        return items

def _compute_trait_ema(attempts, alpha=0.30):
    """
    attempts: list of recent assessments newest->oldest
    returns: trait_scores dict
    """
    # reverse so oldest -> newest for EMA
    attempts = list(reversed(attempts))

    trait = None
    for a in attempts:
        scores = (a.get("results", {}) or {}).get("scores", {}) or {}
        if not scores:
            continue
        if trait is None:
            trait = {k: float(v) for k, v in scores.items()}
        else:
            for k, v in scores.items():
                trait[k] = (1 - alpha) * trait.get(k, 0.0) + alpha * float(v)

    return trait or {}


def gift_assessment_ui():
    st.subheader("🧪 Spiritual Gifts Assessment")

    # Ensure user is authenticated
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
        return

    current_user_id = st.session_state.user_id
    recent = fetch_recent_gift_assessments(current_user_id, limit=5)
    trait_scores = _compute_trait_ema(recent, alpha=0.30)

    # Trait top3
    trait_top3 = sorted(trait_scores.items(), key=lambda kv: kv[1], reverse=True)[:3]
    trait_top3 = r.get("trait_top3")
    if trait_top3:
        st.markdown("#### Stable Trait Top 3 (across retakes)")
        for i, item in enumerate(trait_top3, 1):
            st.markdown(f"- {i}. **{item.get('gift')}** (trait: {round(float(item.get('score', 0.0)), 3)})")

    # --- Display Previous Assessment Results ---
    results = {
        ...
        "confidence": _confidence_label(float(final.margin)),
        "trait_scores": trait_scores,
        "trait_top3": [{"gift": g, "score": float(s)} for g, s in trait_top3],
        "trait_engine": "ema_alpha_0.30_last5",
}

    if result:
        r = result.get("results", {}) or {}
        top3 = r.get("top3", []) or []
        with st.expander("🛠 Debug: full saved row"):
            st.json(result)

        st.markdown("### 💡 Your Last Spiritual Gifts Result")
        margin = r.get("margin", 0.0)
        try:
            margin = float(margin)
        except Exception:
            margin = 0.0

        conf = _confidence_label(margin)
        st.info(
            f"- 🧠 Primary Gift: **{r.get('primary_gift', 'N/A')}**\n"
            f"- 🌟 Secondary Gift: **{r.get('secondary_gift', 'N/A')}**\n"
            f"- 🎯 Confidence: **{conf}** (margin: {round(margin, 3)})"
        )


        if top3:
            st.markdown("#### Top 3 Gifts")
            for i, item in enumerate(top3, 1):
                gift = item.get("gift", "N/A")
                score = item.get("score", 0.0)
                try:
                    score = float(score)
                except Exception:
                    score = 0.0
                st.markdown(f"- {i}. **{gift}** (score: {round(score, 3)})")

        col1, col2 = st.columns(2)

        with col1:
            user_name_for_report = st.session_state.get("user_name", "N/A")

            report_lines = [
                "Tukuza Yesu Spiritual Gifts Report",
                "",
                f"User Name: {user_name_for_report}",
                "",
                f"Primary Gift: {r.get('primary_gift', 'N/A')}",
                f"Secondary Gift: {r.get('secondary_gift', 'N/A')}",
                "",
                "Top 3:",
            ]

            for i, item in enumerate(top3, 1):
                gift = item.get("gift", "N/A")
                score = item.get("score", 0.0)
                try:
                    score = float(score)
                except Exception:
                    score = 0.0
                report_lines.append(f"{i}. {gift} (score: {round(score, 3)})")

            report_lines += [
                "",
                "Note:",
                "This assessment identifies edification gifts for serving and building up the body of Christ.",
                "It does not determine fivefold office calling.",
                "",
                "Built with faith by Sammy Karuri | Tukuza Yesu AI Toolkit",
            ]

            st.download_button(
                "⬇️ Download Gifts Report",
                "\n".join(report_lines),
                file_name=f"tukuza_gifts_report_{str(user_name_for_report).replace(' ', '_').lower()}.txt",
                mime="text/plain",
                key=f"download_gifts_report_{current_user_id}",
            )

        with col2:
            if st.button("🧹 Clear Previous Gifts Result", key=f"clear_gifts_{current_user_id}"):
                delete_gift_assessment_for_user(current_user_id)
                st.success("Cleared.")
                st.rerun()

    st.markdown("---")

    # --- New Assessment Form ---
    st.subheader("Take a New Spiritual Gifts Assessment")

    sample_input = st.text_input(
        "🌐 Type anything in your language to personalize the experience:",
        key="sample_lang_input_assessment",
    )
    user_lang = _detect_language(sample_input)

    scale_instruction = "Answer each question on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree)."
    if user_lang != "en":
        try:
            scale_instruction = GoogleTranslator(source="en", target=user_lang).translate(scale_instruction)
        except Exception:
            pass

    st.caption(scale_instruction)
    st.caption("This section measures edification gifts (not fivefold office calling).")

    questions = _translate_list(QUESTIONS_EN, user_lang)

    # --- Core Form ---
with st.form("gifts_core_form"):
    responses = [
        st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"gift_core_{i}_{current_user_id}")
        for i, q in enumerate(questions)
    ]
    submitted = st.form_submit_button("🎯 Calculate My Gifts")

if submitted:
    base = score_gifts(responses)

    # Save the attempt in session_state so tie-breaker can run on next submit
    st.session_state["gifts_last_responses"] = responses
    st.session_state["gifts_pending_base"] = {
        "primary": base.primary,
        "secondary": base.secondary,
        "needs_tiebreak": base.needs_tiebreak,
    }

    # Also store the base scores/top3 in a safe json form (so we can rebuild)
    st.session_state["gifts_pending_base_full"] = {
        "scores": {k: float(v) for k, v in base.scores.items()},
        "top3": [{"gift": g, "score": float(s)} for g, s in base.top3],
        "primary": base.primary,
        "secondary": base.secondary,
        "margin": float(base.margin),
        "needs_tiebreak": bool(base.needs_tiebreak),
    }

    # If no tie-break needed, save immediately
    if not base.needs_tiebreak:
        results = {
            "engine": "gifts_v2_deterministic",
            "primary_gift": base.primary,
            "secondary_gift": base.secondary,
            "top3": [{"gift": g, "score": float(s)} for g, s in base.top3],
            "scores": {k: float(v) for k, v in base.scores.items()},
            "margin": float(base.margin),
            "used_tiebreak": False,
        }

        insert_gift_assessment(
            session_id=str(current_user_id),
            language=str(user_lang),
            answers={"responses": responses},
            results=results,
        )

        # clear pending
        st.session_state.pop("gifts_pending_base", None)
        st.session_state.pop("gifts_pending_base_full", None)
        st.session_state.pop("gifts_last_responses", None)

        st.success("✅ Saved! Your results will appear above.")
        st.rerun()

# --- Tie-breaker Form (OUTSIDE the core submit block) ---
pending = st.session_state.get("gifts_pending_base_full")

if pending and pending.get("needs_tiebreak"):
    st.warning("Your top two gifts are very close. Answer 6 quick tie-breaker questions for accuracy.")
    st.caption("Scroll down to answer the 6 tie-breaker questions, then click “Finalize Result.”")

    primary = pending["primary"]
    secondary = pending["secondary"]

    tp = _translate_list(TIEBREAKER[primary], user_lang)
    ts = _translate_list(TIEBREAKER[secondary], user_lang)

    with st.form("gifts_tiebreak_form"):
        st.markdown(f"### Tie-breaker: {primary}")
        tie_primary = [
            st.slider(q, 1, 5, 3, key=f"tie_{primary}_{j}_{current_user_id}")
            for j, q in enumerate(tp)
        ]

        st.markdown(f"### Tie-breaker: {secondary}")
        tie_secondary = [
            st.slider(q, 1, 5, 3, key=f"tie_{secondary}_{j}_{current_user_id}")
            for j, q in enumerate(ts)
        ]

        tie_submit = st.form_submit_button("✅ Finalize Result")

    if tie_submit:
        # rebuild GiftResult from stored base
        from modules.gifts_engine import GiftResult

        base_obj = GiftResult(
            scores=pending["scores"],
            top3=[(x["gift"], x["score"]) for x in pending["top3"]],
            primary=pending["primary"],
            secondary=pending["secondary"],
            margin=pending["margin"],
            needs_tiebreak=True,
        )

        final = apply_tiebreak(base_obj, tie_primary, tie_secondary)

        responses = st.session_state.get("gifts_last_responses", [])

        results = {
            "engine": "gifts_v2_deterministic",
            "primary_gift": final.primary,
            "secondary_gift": final.secondary,
            "top3": [{"gift": g, "score": float(s)} for g, s in final.top3],
            "scores": {k: float(v) for k, v in final.scores.items()},
            "margin": float(final.margin),
            "used_tiebreak": True,
        }

        insert_gift_assessment(
            session_id=str(current_user_id),
            language=str(user_lang),
            answers={"responses": responses},
            results=results,
        )

        # clear pending
        st.session_state.pop("gifts_pending_base", None)
        st.session_state.pop("gifts_pending_base_full", None)
        st.session_state.pop("gifts_last_responses", None)

        st.success("✅ Saved! Your finalized results will appear above.")
        st.rerun()
