from transformers import pipeline
import streamlit as st

# ---------------------------
# 🤗 Hugging Face Pipelines
# ---------------------------

@st.cache_resource
def load_classifier_model():
    """
    Loads a zero-shot classification model from Hugging Face.
    """
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

@st.cache_resource
def load_sentiment_model():
    """
    Loads a sentiment analysis model from Hugging Face.
    """
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Initialize once for global use
classifier = load_classifier_model()
sentiment_analyzer = load_sentiment_model()
def classify_text(text, candidate_labels):
    """
    Classifies the input text into one of the candidate labels.
    """
    return classifier(text, candidate_labels)