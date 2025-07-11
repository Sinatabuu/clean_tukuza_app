# 📁 MODULE: user_profile.py
import streamlit as st
import uuid
import json
import os

PROFILE_FILE = "user_profiles.json"

# Load or initialize profile storage
def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def create_or_load_profile():
    profiles = load_profiles()

    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())

    user_id = st.session_state.user_id

    # Ask for basic user info if not already stored
    if user_id not in profiles:
        st.subheader("👤 Create Your Discipleship Profile")

        name = st.text_input("Your Name")
        age = st.number_input("Your Age", min_value=10, max_value=100, step=1)
        stage = st.selectbox("Your Faith Stage", [
            "New Believer", "Growing Disciple", "Ministry Ready", "Faith Leader"
        ])

        if st.button("✅ Save Profile"):
            profiles[user_id] = {
                "name": name,
                "age": age,
                "stage": stage,
                "history": []
            }
            save_profiles(profiles)
            st.success("Profile created successfully!")

    else:
        profile = profiles[user_id]
        st.success(f"Welcome back, {profile['name']} - {profile['stage']}")
        st.json(profile)

    return profiles
