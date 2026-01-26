import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load dataset
data = pd.read_csv("disease_dataset.csv")

# Clean column names (VERY IMPORTANT)
data.columns = data.columns.str.strip()

# Automatically select target column
TARGET = "prognosis"

# Split features and label
X = data.drop(TARGET, axis=1)
y = data[TARGET]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print("Model Accuracy:", round(accuracy, 4))

# Save model
joblib.dump(model, "disease_prediction_model.pkl")
joblib.dump(X.columns.tolist(), "symptom_list.pkl")

print("Model saved as disease_prediction_model.pkl")
print("Symptom list saved as symptom_list.pkl")