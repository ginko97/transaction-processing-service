import pandas as pd
import numpy as np


def create_features(df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
    """Create features for fraud detection - works for training and prediction."""
    df = df.copy()

    # Convert Decimal to float
    if "amount" in df.columns:
        df["amount"] = df["amount"].astype(float)

    # Basic features
    df["amount_log"] = np.log1p(df["amount"])
    df["risk_score_scaled"] = df.get("risk_score", 50) / 100.0

    # Frequency features
    if is_training and "customer_id" in df.columns and len(df) > 1:
        df["tx_count_customer"] = df.groupby("customer_id")["transaction_id"].transform(
            "count"
        )
        df["avg_amount_customer"] = df.groupby("customer_id")["amount"].transform(
            "mean"
        )
        df["amount_vs_avg_customer"] = df["amount"] - df["avg_amount_customer"]
    else:
        df["tx_count_customer"] = 1
        df["avg_amount_customer"] = df["amount"]
        df["amount_vs_avg_customer"] = 0.0

    # Risk level
    df["risk_level"] = pd.cut(
        df.get("risk_score", 50),
        bins=[0, 30, 60, 100],
        labels=["low", "medium", "high"],
    )

    # Time features
    if "created_at" in df.columns:
        df["hour"] = pd.to_datetime(df["created_at"]).dt.hour
        df["is_night"] = df["hour"].isin([0, 1, 2, 3, 4, 23]).astype(int)
    else:
        df["hour"] = 12
        df["is_night"] = 0

    # Flags
    df["high_amount_flag"] = (df["amount"] > 5000).astype(int)
    df["high_risk_flag"] = (df.get("risk_score", 0) > 70).astype(int)

    return df
