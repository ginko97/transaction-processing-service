from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Transaction amount (must be > 0)")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO currency code e.g. USD"
    )
    merchant_id: str = Field(..., min_length=1, max_length=50)
    customer_id: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class TransactionValidateRequest(TransactionBase):
    card_last4: Optional[str] = Field(None, min_length=4, max_length=4)


class TransactionValidateResponse(BaseModel):
    status: str = Field(..., pattern="^(approved|declined|review)$")
    transaction_id: str
    risk_score: float = Field(..., ge=0, le=100)
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
