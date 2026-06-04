import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

# Simple imports (adjust if needed)
from app.models.transaction import TransactionModel
from app.ml.features.feature_engineering import create_features


def extract_transactions(db: Session, limit: int = 10000) -> pd.DataFrame:
    """Extract data from PostgreSQL."""
    query = db.query(TransactionModel)
    df = pd.read_sql(query.statement, db.bind)
    print(f"✅ Extracted {len(df)} transactions")
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and transform data."""
    df = df.copy()
    df["amount"] = df["amount"].astype(float)
    df = create_features(df, is_training=True)
    print("✅ Data transformation completed")
    return df


def load_to_parquet(df: pd.DataFrame, filename: str | None = None) -> str:
    """Save clean data to Parquet."""
    if filename is None:
        filename = (
            f"data/clean_transactions_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet"
        )

    df.to_parquet(filename, index=False)
    print(f"✅ Data saved to {filename}")
    return filename


# Quick test
if __name__ == "__main__":
    from app.core.database import SessionLocal

    db = SessionLocal()
    df = extract_transactions(db)
    df = transform_data(df)
    load_to_parquet(df)
    db.close()
