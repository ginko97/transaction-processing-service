import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.transaction import TransactionModel
from app.ml.features.feature_engineering import create_features
from app.core.logger import logger


def run_data_quality_checks(df: pd.DataFrame) -> dict:
    """Simple data quality checks."""
    checks = {
        "total_rows": len(df),
        "null_values": int(df.isnull().sum().sum()),
        "duplicate_transactions": int(df["transaction_id"].duplicated().sum())
        if "transaction_id" in df.columns
        else 0,
        "negative_amounts": int((df["amount"] < 0).sum())
        if "amount" in df.columns
        else 0,
        "invalid_risk_score": int(
            ((df["risk_score"] < 0) | (df["risk_score"] > 100)).sum()
        )
        if "risk_score" in df.columns
        else 0,
    }

    success_rate = (
        sum(1 for v in checks.values() if v == 0) / len(checks) * 100 if checks else 0
    )

    logger.info(
        "Data Quality Check Completed",
        extra={"success_rate": round(success_rate, 2), **checks},
    )
    print(f"Data Quality Checks - Success Rate: {success_rate:.1f}%")

    return checks


def run_etl_pipeline(db: Session) -> str:
    """Main ETL pipeline with logging and error handling."""
    try:
        logger.info("Starting ETL pipeline")

        df = extract_transactions(db)
        df = transform_data(df)
        run_data_quality_checks(df)
        filename = load_to_parquet(df)

        logger.info(
            "ETL pipeline completed successfully", extra={"output_file": filename}
        )
        return filename

    except Exception:
        logger.error("ETL pipeline failed", exc_info=True)
        raise


# Helper functions (same as before)
def extract_transactions(db: Session, limit: int = 10000) -> pd.DataFrame:
    query = db.query(TransactionModel)
    df = pd.read_sql(query.statement, db.bind)
    print(f"Extracted {len(df)} transactions")
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["amount"] = df["amount"].astype(float)
    df = create_features(df, is_training=True)
    print("Data transformation completed")
    return df


def load_to_parquet(df: pd.DataFrame, filename: str | None = None) -> str:
    """Save clean data to Parquet with Spark compatibility."""
    if filename is None:
        filename = (
            f"data/clean_transactions_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet"
        )

    df = df.copy()

    # Fix timestamp for Spark compatibility
    if "created_at" in df.columns:
        df["created_at"] = (
            pd.to_datetime(df["created_at"])
            .dt.tz_localize(None)
            .astype("datetime64[ms]")
        )

    # Save with Spark-compatible settings
    df.to_parquet(filename, index=False, compression="snappy", engine="pyarrow")
    print(f"Data saved to {filename} (Spark compatible)")
    return filename


# Quick test
if __name__ == "__main__":
    from app.core.database import SessionLocal

    db = SessionLocal()
    run_etl_pipeline(db)
    db.close()
