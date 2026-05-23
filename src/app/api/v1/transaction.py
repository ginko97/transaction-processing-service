from fastapi import APIRouter, HTTPException, Depends
from uuid import uuid4
import re
from sqlalchemy.orm import Session

from ...schemas.transaction import (
    TransactionValidateRequest,
    TransactionValidateResponse,
    ErrorResponse,
)
from ...core.logger import logger
from ...core.database import get_db
from ...models.transaction import TransactionModel

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/validate",
    response_model=TransactionValidateResponse,
    responses={400: {"model": ErrorResponse}},
)
async def validate_transaction(
    request: TransactionValidateRequest, db: Session = Depends(get_db)
):
    """Validate payment transaction and save to database."""
    try:
        logger.info(
            "Transaction validation request received",
            extra={
                "amount": str(request.amount),
                "currency": request.currency,
                "merchant_id": request.merchant_id,
            },
        )

        # Risk scoring logic
        risk_score = 12.0
        if request.amount > 10000:
            risk_score = 82.0
        elif request.amount > 5000:
            risk_score += 35.0
        if request.currency != "USD":
            risk_score += 18.0
        if request.card_last4 and re.match(r"^4[0-9]{3}$", request.card_last4):
            risk_score -= 5.0

        status = (
            "approved"
            if risk_score < 60
            else "review"
            if risk_score < 80
            else "declined"
        )

        transaction_id = str(uuid4())

        # Save to database
        db_transaction = TransactionModel(
            transaction_id=transaction_id,
            amount=request.amount,
            currency=request.currency,
            merchant_id=request.merchant_id,
            customer_id=request.customer_id,
            description=request.description,
            risk_score=risk_score,
            status=status,
        )
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        response = TransactionValidateResponse(
            status=status,
            transaction_id=transaction_id,
            risk_score=round(risk_score, 2),
            reason="High amount" if risk_score >= 60 else None,
        )

        logger.info(
            "Transaction validated and saved",
            extra={"status": status, "risk_score": response.risk_score},
        )
        return response

    except Exception as e:
        logger.error("Validation error", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
