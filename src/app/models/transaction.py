from sqlalchemy import Column, Integer, String, Float, DateTime, Text, DECIMAL
from datetime import datetime, timezone
from ..core.database import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(36), unique=True, nullable=False, index=True)
    amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    merchant_id = Column(String(50), nullable=False)
    customer_id = Column(String(50))
    description = Column(Text)
    risk_score = Column(Float)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
