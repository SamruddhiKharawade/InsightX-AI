"""
Loads the saved churn model and generates churn probability predictions
for every customer, with a plain-language risk level and the top global
factors driving the model's predictions.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

import joblib
import pandas as pd

from src.features.churn_features import build_churn_features
from src.models.churn.train_churn_model import prepare_data

MODEL_DIR = Path(__file__).resolve().parent


def risk_level(prob: float) -> str:
    if prob >= 0.7:
        return "HIGH"
    if prob >= 0.4:
        return "MEDIUM"
    return "LOW"


def predict_for_customers(customer_ids: list = None) -> pd.DataFrame:
    model = joblib.load(MODEL_DIR / "churn_model.pkl")
    scaler = joblib.load(MODEL_DIR / "churn_scaler.pkl")
    feature_cols = joblib.load(MODEL_DIR / "churn_feature_cols.pkl")

    df = build_churn_features()
    X, _, _ = prepare_data(df)
    # Align columns exactly to what the model was trained on, in the same order
    X = X.reindex(columns=feature_cols, fill_value=0)
    X_scaled = scaler.transform(X)

    df["churn_probability"] = model.predict_proba(X_scaled)[:, 1]
    df["risk_level"] = df["churn_probability"].apply(risk_level)

    result = df[["customer_id", "customer_name", "churn_probability", "risk_level"]]
    if customer_ids:
        result = result[result["customer_id"].isin(customer_ids)]

    return result.sort_values("churn_probability", ascending=False)


if __name__ == "__main__":
    results = predict_for_customers()
    print(results.head(10).to_string(index=False))

    model = joblib.load(MODEL_DIR / "churn_model.pkl")
    if hasattr(model, "feature_importances_"):
        feature_cols = joblib.load(MODEL_DIR / "churn_feature_cols.pkl")
        importances = pd.Series(
            model.feature_importances_, index=feature_cols
        ).sort_values(ascending=False)
        print("\nTop factors driving churn predictions overall:")
        print(importances.head(8).to_string())