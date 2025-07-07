import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib
import os

# 🔄 Load your verse dataset
data_path = "data/verse_training_data.csv"  # update path if needed
df = pd.read_csv(data_path)

# 🧹 Clean missing data
df = df.dropna(subset=["verse", "label"])

# ✨ Vectorization and classification pipeline
vectorizer = TfidfVectorizer(stop_words='english')
X = vectorizer.fit_transform(df["verse"])
y = df["label"]

# 📦 Save vectorizer
os.makedirs("models", exist_ok=True)
joblib.dump(vectorizer, "models/vectorizer.pkl")

# Optional: Train and save a classifier too
model = LogisticRegression(max_iter=1000)
model.fit(X, y)
joblib.dump(model, "models/model.pkl")

print("✅ vectorizer.pkl and model.pkl saved to /models/")
