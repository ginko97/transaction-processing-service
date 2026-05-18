from fastapi import APIRouter, HTTPException
from uuid import uuid4
import re

from ...schemas.transaction import (
    TransactionValidateRequest,
    TransactionValidateResponse,
    ErrorResponse,
)
from ...core.logger import logger

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/validate",
    response_model=TransactionValidateResponse,
    responses={400: {"model": ErrorResponse}},
)
async def validate_transaction(request: TransactionValidateRequest):
    """Validate payment transaction with basic business + risk rules."""
    try:
        logger.info(
            "Transaction validation request received",
            extra={
                "amount": str(request.amount),
                "currency": request.currency,
                "merchant_id": request.merchant_id,
            },
        )

        # Simple rule engine (will be replaced with ML model in Week 4)
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

        response = TransactionValidateResponse(
            status=status,
            transaction_id=str(uuid4()),
            risk_score=round(risk_score, 2),
            reason="High amount" if risk_score >= 60 else None,
        )

        logger.info(
            "Transaction validated",
            extra={"status": status, "risk_score": response.risk_score},
        )
        return response

    except Exception as e:
        logger.error("Validation error", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
