import pandas as pd
from sqlalchemy.orm import Session
from ...models.transaction import TransactionModel


def load_transactions_for_training(db: Session, limit: int = 10000) -> pd.DataFrame:
    """Load transactions from database for ML training."""
    query = db.query(TransactionModel).limit(limit)
    df = pd.read_sql(query.statement, db.bind)

    # Rename for easier use
    df = df.rename(
        columns={
            "transaction_id": "transaction_id",
            "amount": "amount",
            "risk_score": "risk_score",
            "status": "status",
            "customer_id": "customer_id",
            "merchant_id": "merchant_id",
            "created_at": "created_at",
        }
    )

    return df
