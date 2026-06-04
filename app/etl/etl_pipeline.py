import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.transaction import TransactionModel
from app.ml.features.feature_engineering import create_features


def run_data_quality_checks(df: pd.DataFrame) -> dict:
    """Simple but effective data quality checks."""
    checks = {}

    checks["total_rows"] = len(df)
    checks["null_values"] = df.isnull().sum().sum()
    checks["duplicate_transactions"] = (
        df["transaction_id"].duplicated().sum() if "transaction_id" in df.columns else 0
    )
    checks["negative_amounts"] = (
        (df["amount"] < 0).sum() if "amount" in df.columns else 0
    )
    checks["invalid_risk_score"] = (
        ((df["risk_score"] < 0) | (df["risk_score"] > 100)).sum()
        if "risk_score" in df.columns
        else 0
    )
    checks["invalid_currency"] = (
        (~df["currency"].isin(["USD", "SGD", "EUR", "IDR"])).sum()
        if "currency" in df.columns
        else 0
    )

    success_rate = (
        sum(1 for v in checks.values() if v == 0) / len(checks) * 100 if checks else 0
    )

    print(f"Data Quality Checks Completed - Success Rate: {success_rate:.1f}%")
    for key, value in checks.items():
        print(f"   {key}: {value}")

    return checks


def extract_transactions(db: Session, limit: int = 10000) -> pd.DataFrame:
    """Extract data from PostgreSQL."""
    query = db.query(TransactionModel)
    df = pd.read_sql(query.statement, db.bind)
    print(f"Extracted {len(df)} transactions")
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform and clean data."""
    df = df.copy()
    df["amount"] = df["amount"].astype(float)
    df = create_features(df, is_training=True)
    print("Data transformation completed")
    return df


def load_to_parquet(df: pd.DataFrame, filename: str | None = None) -> str:
    """Save clean data to Parquet."""
    if filename is None:
        filename = (
            f"data/clean_transactions_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet"
        )

    df.to_parquet(filename, index=False)
    print(f"Data saved to {filename}")
    return filename


# Main ETL Pipeline
if __name__ == "__main__":
    from app.core.database import SessionLocal

    db = SessionLocal()

    # Run ETL Pipeline
    df = extract_transactions(db)
    df = transform_data(df)

    # Run Data Quality Check
    run_data_quality_checks(df)

    # Load clean data
    load_to_parquet(df)

    db.close()
