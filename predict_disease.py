import joblib
import pandas as pd

# Load model and symptom list
model = joblib.load("disease_prediction_model.pkl")
symptoms = joblib.load("symptom_list.pkl")

# Example: extracted symptoms from your system
extracted_symptoms = [
    "chest_pain",
    "shortness_of_breath",
    "nausea",
    "anxiety",
    "sweating",
    "upper_body_pain"
    
]

# Encode symptoms into vector
input_vector = [1 if symptom in extracted_symptoms else 0 for symptom in symptoms]

# Convert to DataFrame
input_df = pd.DataFrame([input_vector], columns=symptoms)

# Predict disease
prediction = model.predict(input_df)[0]
probabilities = model.predict_proba(input_df)[0]
confidence = max(probabilities)

print("Predicted Disease:", prediction)
print("Confidence:", round(confidence, 2))