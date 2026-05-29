import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib

from src.app.ml.features.feature_engineering import create_features
from src.app.ml.data.loader import load_transactions_for_training
from src.app.core.database import SessionLocal


def train_fraud_model(db, test_size: float = 0.3):
    """Train XGBoost fraud detection model - handles small datasets."""
    df = load_transactions_for_training(db, limit=10000)
    df = create_features(df)

    if len(df) < 3:
        print("Not enough data. Add more transactions via /validate endpoint.")
        return None

    # Create target
    df["is_fraud"] = ((df["risk_score"] >= 70) | (df["status"] == "declined")).astype(
        int
    )

    feature_cols = [
        "amount",
        "amount_log",
        "risk_score",
        "risk_score_scaled",
        "tx_count_customer",
        "avg_amount_customer",
        "amount_vs_avg_customer",
        "hour",
        "is_night",
        "high_amount_flag",
        "high_risk_flag",
    ]

    X = df[feature_cols]
    y = df["is_fraud"]

    print(f"Total samples: {len(df)} | Fraud cases: {y.sum()}")

    # Handle small data
    if len(df) < 10 or y.nunique() < 2:
        print("Using all data for training (too few samples for splitting)")
        X_train, X_test, y_train, y_test = X, X.iloc[:1], y, y.iloc[:1]
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=42,
            stratify=None,  # Disable stratify for small data
        )

    # Train model
    model = XGBClassifier(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric="auc",
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    print("\n=== Fraud Detection Model Training Complete ===")
    print(
        "ROC AUC Score:",
        roc_auc_score(y_test, y_pred_proba) if len(y_test) > 1 else "N/A (small data)",
    )
    print(
        "\nClassification Report:\n",
        classification_report(y_test, y_pred, zero_division=0),
    )

    # Save model
    model_path = "models/fraud_model_latest.joblib"
    joblib.dump(model, model_path)
    print(f"Model saved to: {model_path}")

    return model


# For quick test
if __name__ == "__main__":
    db = SessionLocal()
    train_fraud_model(db)
    db.close()
