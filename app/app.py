import os
import sys
import streamlit as st

# Ensure repo root on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import modules.db as db

st.set_page_config(page_title="Tukuza Yesu AI Toolkit", page_icon="📖", layout="wide")

@st.cache_resource
def init_db_once():
    db.run_schema_upgrades()
    return True

init_db_once()

def safe_load(func_import):
    """Return (callable, error) without crashing app."""
    try:
        return func_import(), None
    except Exception as e:
        return None, e

def get_sentiment_model():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def get_zero_shot_classifier():
    from transformers import pipeline
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def main_app():
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None

    st.sidebar.title("✝️ Tukuza Yesu Toolkit 🚀")

    # --- LOGIN (keep it simple first) ---
    if st.session_state.user_id is None:
        st.header("Welcome to Tukuza!")
        st.info("Login/Profiles coming next — for now we’ll use a session-based user.")
        if st.button("Continue"):
            st.session_state.user_id = st.session_state.get("session_id", "demo")
            st.session_state.user_name = "Guest"
        st.stop()

    st.sidebar.write(f"Logged in as: **{st.session_state.user_name}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.rerun()

    tool = st.sidebar.selectbox(
        "🛠️ Select a Tool",
        [
            "🏠 Dashboard",
            "📖 BibleBot",
            "📘 Spiritual Growth Tracker",
            "🔖 Verse Classifier",
            "🌅 Daily Verse",
            "🧪 Spiritual Gifts Assessment",
        ],
    )

    if tool == "🏠 Dashboard":
        st.title("Tukuza Yesu AI Toolkit")
        st.write("Select a tool from the sidebar.")

    elif tool == "📖 BibleBot":
        try:
            from modules.biblebot_ui import biblebot_ui
            biblebot_ui()
        except Exception as e:
            st.error("BibleBot failed to load.")
            st.exception(e)


    elif tool == "📘 Spiritual Growth Tracker":
        ui, err = safe_load(lambda: __import__("modules.growth_tracker_ui", fromlist=["growth_tracker_ui"]).growth_tracker_ui)
        if err:
            st.error("Growth Tracker failed to load.")
            st.exception(err)
        else:
            # load sentiment only when needed
            with st.spinner("Loading sentiment model..."):
                sentiment = get_sentiment_model()
            ui(sentiment)

    elif tool == "🔖 Verse Classifier":
        st.subheader("Classify a Bible Verse")
        verse = st.text_area("Paste a Bible verse here:")
        if st.button("Classify"):
            if not verse.strip():
                st.warning("Please enter a verse.")
            else:
                with st.spinner("Loading classifier..."):
                    clf = get_zero_shot_classifier()
                labels = ["faith","love","hope","salvation","guidance","suffering","peace","justice","community","forgiveness"]
                result = clf(verse, candidate_labels=labels, multi_label=False)
                st.success(f"Predicted Topic: **{result['labels'][0]}** (Confidence: {result['scores'][0]:.2f})")

    elif tool == "🌅 Daily Verse":
        st.subheader("🌞 Your Daily Verse")
        st.success("“This is the day that the Lord has made; let us rejoice and be glad in it.” – Psalm 118:24")

    elif tool == "🧪 Spiritual Gifts Assessment":
        ui, err = safe_load(lambda: __import__("modules.gift_assessment", fromlist=["gift_assessment_ui"]).gift_assessment_ui)
        if err:
            st.error("Gift Assessment failed to load.")
            st.exception(err)
        else:
            ui()

main_app()

st.markdown("---")
st.caption("Built with faith by **Sammy Karuri** | Tukuza Yesu AI Toolkit 🌐")
