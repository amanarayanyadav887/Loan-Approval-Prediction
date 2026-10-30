from pathlib import Path
import warnings

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import os
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ARTIFACT_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "loan_model.joblib"

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
model = None
feature_columns = None
model_accuracy = None
training_rows = None


def prepare_training_data():
    """Reproduce the feature preparation used in loan.ipynb."""
    source = DATA_DIR / "Loan_Risk_Working.csv"
    if not source.exists():
        source = DATA_DIR / "cleaned_loan_data.csv"
    if not source.exists():
        raise FileNotFoundError("No CSV found in the data folder.")

    df = pd.read_csv(source)

    # Same missing-value treatment as the notebook's data-cleaning cells.
    df["Income"] = df["Income"].fillna(df["Income"].median())
    df["CreditScore"] = df["CreditScore"].fillna(df["CreditScore"].median())
    df["Education"] = df["Education"].fillna(df["Education"].mode()[0])

    # Same columns dropped and same one-hot encoding approach as the notebook.
    model_df = df.drop(columns=["City", "Age", "YearsExperience", "Education", "Gender"])
    encoded_df = pd.get_dummies(model_df, columns=["EmploymentType"], dtype=int)

    X = encoded_df.drop(columns=["LoanApproved"])
    y = encoded_df["LoanApproved"]
    return X, y, len(df)


def load_or_train_model():
    global model, feature_columns, model_accuracy, training_rows

    if MODEL_PATH.exists():
        saved = joblib.load(MODEL_PATH)
        if isinstance(saved, dict) and "model" in saved and "feature_columns" in saved:
            model = saved["model"]
            feature_columns = list(saved["feature_columns"])
            # Accuracy is not stored in the notebook export.
            training_rows = None
            return

    X, y, training_rows = prepare_training_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Keep LogisticRegression's notebook defaults to match the original model.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = LogisticRegression()
        model.fit(X_train, y_train)

    feature_columns = list(X.columns)
    model_accuracy = float(accuracy_score(y_test, model.predict(X_test)))

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "feature_columns": feature_columns},
        MODEL_PATH
    )


def make_prediction(payload):
    income = float(payload["income"])
    loan_amount = float(payload["loan_amount"])
    credit_score = float(payload["credit_score"])
    employment_type = str(payload["employment_type"])

    if income < 0 or loan_amount < 0:
        raise ValueError("Income and loan amount must be zero or greater.")
    if not 300 <= credit_score <= 850:
        raise ValueError("Credit score must be between 300 and 850.")

    row = {
        "Income": income,
        "LoanAmount": loan_amount,
        "CreditScore": credit_score,
        "EmploymentType_Salaried": int(employment_type == "Salaried"),
        "EmploymentType_Self-Employed": int(employment_type == "Self-Employed"),
        "EmploymentType_Unemployed": int(employment_type == "Unemployed"),
    }
    input_df = pd.DataFrame([row]).reindex(columns=feature_columns, fill_value=0)

    prediction = int(model.predict(input_df)[0])
    probability = None
    if hasattr(model, "predict_proba"):
        probability = float(model.predict_proba(input_df)[0][list(model.classes_).index(1)])

    return {
        "prediction": prediction,
        "label": "Likely to be approved" if prediction == 1 else "Likely not to be approved",
        "approval_probability": probability,
    }


@app.route("/")
def home():
    return render_template("index.html", model_accuracy=model_accuracy, training_rows=training_rows)


@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json(force=True)
        result = make_prediction(payload)
        return jsonify(result)
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc) or "Please check the values and try again."}), 400
    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify({"error": "Prediction failed. Check the terminal for details."}), 500


# Load model when imported by Gunicorn on Render.
load_or_train_model()

if __name__ == "__main__":
    print("\\nLoan Approval API is ready.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
