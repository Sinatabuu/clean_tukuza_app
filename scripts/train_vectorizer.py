import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

# Load training data
data = pd.read_csv("app/verse_training_data.csv")  # Make sure this file exists
X = data["verse"]
y = data["label"]

# Create pipeline
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

model = LogisticRegression()
model.fit(X_vec, y)

# Save vectorizer and model
os.makedirs("models", exist_ok=True)
joblib.dump(vectorizer, "models/vectorizer.pkl")
joblib.dump(model, "models/model.pkl")  # Optional if you need a different model
