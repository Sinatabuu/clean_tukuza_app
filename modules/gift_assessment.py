# modules/gift_assessment.py

import streamlit as st
from langdetect import detect
from deep_translator import GoogleTranslator

from modules.db import (
    insert_gift_assessment,
    fetch_latest_gift_assessment,
    delete_gift_assessment_for_user,
    fetch_recent_gift_assessments,
)

from modules.gifts_engine import GiftResult, QUESTIONS_EN, TIEBREAKER, score_gifts, apply_tiebreak

def _mark_finalize():
    st.session_state["gifts_finalize_clicked"] = True

def _confidence_label(margin: float) -> str:
    if margin >= 0.35:
        return "High"
    if margin >= 0.20:
        return "Medium"
    return "Low"


def _detect_language(sample_text: str) -> str:
    if not sample_text or not sample_text.strip():
        return "en"
    try:
        supported = list(GoogleTranslator().get_supported_languages(as_dict=True).values())
        lang = detect(sample_text)
        return lang if lang in supported else "en"
    except Exception:
        return "en"


def _translate_list(items, user_lang: str):
    if user_lang == "en":
        return items
    try:
        tr = GoogleTranslator(source="en", target=user_lang)
        return [tr.translate(x) for x in items]
    except Exception:
        return items


def _compute_trait_ema(attempts, alpha=0.30):
    """
    attempts: list of assessments newest->oldest, each has {results: {scores:{...}}}
    returns: trait_scores dict
    """
    attempts = list(reversed(attempts))  # oldest->newest
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

    # auth
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("⚠️ Please log in or create your discipleship profile before continuing.")
        return

    current_user_id = st.session_state.user_id

    # --- Display previous assessment (latest) ---
    result = fetch_latest_gift_assessment(current_user_id)
    if result:
        r = result.get("results", {}) or {}
        top3 = r.get("top3", []) or []

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

        # ---- Trait stability block (computed from recent attempts) ----
        recent = fetch_recent_gift_assessments(current_user_id, limit=5)
        trait_scores = _compute_trait_ema(recent, alpha=0.30)

        if trait_scores:
            trait_top3 = sorted(trait_scores.items(), key=lambda kv: kv[1], reverse=True)[:3]
            st.markdown("#### Stable Trait Top 3 (across retakes)")
            for i, (g, s) in enumerate(trait_top3, 1):
                st.markdown(f"- {i}. **{g}** (trait: {round(float(s), 3)})")

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
                f"Confidence: {conf} (margin: {round(margin, 3)})",
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

    # --- New Assessment ---
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

        # store for tie-break rerun
        st.session_state["gifts_last_responses"] = responses
        st.session_state["gifts_pending_base"] = {
            "scores": {k: float(v) for k, v in base.scores.items()},
            "top3": [(g, float(s)) for g, s in base.top3],
            "primary": base.primary,
            "secondary": base.secondary,
            "margin": float(base.margin),
            "needs_tiebreak": bool(base.needs_tiebreak),
        }

        if not base.needs_tiebreak:
            # compute trait from recent + this attempt (optional)
            recent = fetch_recent_gift_assessments(current_user_id, limit=5)
            trait_scores = _compute_trait_ema(recent, alpha=0.30)
            trait_top3 = sorted(trait_scores.items(), key=lambda kv: kv[1], reverse=True)[:3] if trait_scores else []

            results = {
                "engine": "gifts_v2_deterministic",
                "primary_gift": base.primary,
                "secondary_gift": base.secondary,
                "top3": [{"gift": g, "score": float(s)} for g, s in base.top3],
                "scores": {k: float(v) for k, v in base.scores.items()},
                "margin": float(base.margin),
                "confidence": _confidence_label(float(base.margin)),
                "used_tiebreak": False,
                "trait_engine": "ema_alpha_0.30_last5",
                "trait_scores": trait_scores,
                "trait_top3": [{"gift": g, "score": float(s)} for g, s in trait_top3],
            }

            insert_gift_assessment(
                session_id=str(current_user_id),
                language=str(user_lang),
                answers={"responses": responses},
                results=results,
            )

            st.session_state.pop("gifts_pending_base", None)
            st.session_state.pop("gifts_last_responses", None)

            st.success("✅ Saved! Your results will appear above.")
            st.rerun()

    # --- Tie-breaker Form (independent) ---
    # --- Tie-breaker (NO form; reliable) ---
    pending = st.session_state.get("gifts_pending_base")
    if pending and pending.get("needs_tiebreak"):
        st.warning("Your top two gifts are very close. Answer 6 quick tie-breaker questions for accuracy.")
        st.caption("Answer the 6 questions below, then click “✅ Finalize Result.”")

        # Create a stable attempt id so widget keys never collide
        if "gifts_attempt_id" not in st.session_state:
            st.session_state["gifts_attempt_id"] = 1

        attempt_id = st.session_state["gifts_attempt_id"]
        primary = pending["primary"]
        secondary = pending["secondary"]

        tp = _translate_list(TIEBREAKER[primary], user_lang)
        ts = _translate_list(TIEBREAKER[secondary], user_lang)

        st.markdown(f"### Tie-breaker: {primary}")
        tie_primary = [
            st.slider(q, 1, 5, 3, key=f"tie_{attempt_id}_{primary}_{j}_{current_user_id}")
            for j, q in enumerate(tp)
        ]

        st.markdown(f"### Tie-breaker: {secondary}")
        tie_secondary = [
            st.slider(q, 1, 5, 3, key=f"tie_{attempt_id}_{secondary}_{j}_{current_user_id}")
            for j, q in enumerate(ts)
        ]

        if st.button("✅ Finalize Result", key=f"finalize_{attempt_id}_{current_user_id}"):
            try:
                base_obj = GiftResult(
                    scores=pending["scores"],
                    top3=pending["top3"],
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
                    "confidence": _confidence_label(float(final.margin)),
                    "used_tiebreak": True,
                }

                with st.spinner("Saving your finalized result..."):
                    insert_gift_assessment(
                        session_id=str(current_user_id),
                        language=str(user_lang),
                        answers={"responses": responses},
                        results=results,
                    )

                # Clear pending so the tie-break section disappears
                st.session_state.pop("gifts_pending_base", None)
                st.session_state.pop("gifts_last_responses", None)

                # Bump attempt id so keys change next time
                st.session_state["gifts_attempt_id"] = attempt_id + 1

                st.success("✅ Saved! Your finalized results will appear above.")
                st.rerun()

            except Exception as e:
                st.error("Finalize failed—details below:")
                st.exception(e)

