"""
Trains and evaluates two churn models: Logistic Regression (interpretable
baseline) and Random Forest (usually stronger, gives feature importance).
Saves whichever model achieves better recall, along with its scaler and
the exact feature column list needed to reproduce predictions later.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                              precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.features.churn_features import build_churn_features
from src.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parent

CATEGORICAL_COLS = ["gender", "city", "customer_segment", "preferred_payment_method"]
NUMERIC_COLS = [
    "age", "tenure_days", "frequency", "monetary", "avg_order_value",
    "avg_discount_used", "avg_delivery_time", "avg_rating", "review_count",
    "campaigns_targeted", "total_marketing_spend", "total_conversions",
]


def prepare_data(df: pd.DataFrame):
    df = pd.get_dummies(df, columns=CATEGORICAL_COLS, drop_first=True)
    feature_cols = NUMERIC_COLS + [
        c for c in df.columns if any(c.startswith(cat + "_") for cat in CATEGORICAL_COLS)
    ]
    X = df[feature_cols]
    y = df["churned"]
    return X, y, feature_cols


def evaluate(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }

    logger.info(f"--- {name} ---")
    for k, v in metrics.items():
        logger.info(f"{k:10s}: {v:.3f}")
    logger.info(f"Confusion matrix:\n{confusion_matrix(y_test, y_pred)}")

    return metrics


def main():
    df = build_churn_features()
    X, y, feature_cols = prepare_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    log_reg = LogisticRegression(max_iter=1000, class_weight="balanced")
    log_reg.fit(X_train_scaled, y_train)
    log_reg_metrics = evaluate("Logistic Regression", log_reg, X_test_scaled, y_test)

    rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    rf.fit(X_train_scaled, y_train)
    rf_metrics = evaluate("Random Forest", rf, X_test_scaled, y_test)

    # Select by recall — see Phase 10 write-up for why recall matters most here
    if rf_metrics["recall"] >= log_reg_metrics["recall"]:
        best_name, best_model = "Random Forest", rf
    else:
        best_name, best_model = "Logistic Regression", log_reg
    logger.info(f"Selected best model by recall: {best_name}")

    joblib.dump(best_model, MODEL_DIR / "churn_model.pkl")
    joblib.dump(scaler, MODEL_DIR / "churn_scaler.pkl")
    joblib.dump(feature_cols, MODEL_DIR / "churn_feature_cols.pkl")

    if hasattr(best_model, "feature_importances_"):
        importances = pd.Series(
            best_model.feature_importances_, index=feature_cols
        ).sort_values(ascending=False)
        logger.info(f"Top 10 feature importances:\n{importances.head(10)}")

    logger.info("Model training complete. Artifacts saved to src/models/churn/")


if __name__ == "__main__":
    main()