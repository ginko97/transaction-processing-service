import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from src.app.models.transaction import TransactionModel
from src.app.ml.features.feature_engineering import create_features


def extract_transactions(db: Session, limit: int = 10000) -> pd.DataFrame:
    """Extract data from PostgreSQL."""
    query = db.query(TransactionModel)
    df = pd.read_sql(query.statement, db.bind)
    print(f"Extracted {len(df)} transactions")
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply data quality + feature engineering."""
    df = df.copy()

    # Data Quality Checks
    df = df.dropna(subset=["amount", "transaction_id"])
    df = df[df["amount"] > 0]

    # Feature Engineering
    df = create_features(df, is_training=True)

    print("Data transformation completed")
    return df


def load_to_parquet(df: pd.DataFrame, filename: str | None = None) -> str:
    """Load clean data to Parquet (Delta Lake ready)."""
    if filename is None:
        filename = (
            f"data/clean_transactions_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet"
        )

    df.to_parquet(filename, index=False)
    print(f"Data saved to {filename}")
    return filename


# Quick test function
if __name__ == "__main__":
    from src.app.core.database import SessionLocal

    db = SessionLocal()
    df = extract_transactions(db)
    df = transform_data(df)
    load_to_parquet(df)
    db.close()
