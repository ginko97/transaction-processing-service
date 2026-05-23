from fastapi import APIRouter, HTTPException, Depends
from uuid import uuid4
import re
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...schemas.transaction import (
    TransactionValidateRequest,
    TransactionValidateResponse,
    ErrorResponse,
)
from ...schemas.stats import TransactionStatsResponse, RiskDistribution
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


@router.get("/stats", response_model=TransactionStatsResponse)
async def get_transaction_stats(db: Session = Depends(get_db)):
    """Return advanced statistical analysis of transactions."""
    try:
        # Basic aggregates
        total_tx = db.query(func.count(TransactionModel.id)).scalar() or 0
        total_amount = db.query(func.sum(TransactionModel.amount)).scalar() or 0.0
        avg_amount = db.query(func.avg(TransactionModel.amount)).scalar() or 0.0
        max_amount = db.query(func.max(TransactionModel.amount)).scalar() or 0.0
        min_amount = db.query(func.min(TransactionModel.amount)).scalar() or 0.0
        avg_risk = db.query(func.avg(TransactionModel.risk_score)).scalar() or 0.0
        high_risk = (
            db.query(func.count(TransactionModel.id))
            .filter(TransactionModel.risk_score >= 70)
            .scalar()
            or 0
        )

        # Status & Currency distribution
        status_dist = dict(
            db.query(TransactionModel.status, func.count(TransactionModel.id))
            .group_by(TransactionModel.status)
            .all()
        )
        currency_dist = dict(
            db.query(TransactionModel.currency, func.count(TransactionModel.id))
            .group_by(TransactionModel.currency)
            .all()
        )

        # Risk Distribution
        low_risk = (
            db.query(func.count(TransactionModel.id))
            .filter(TransactionModel.risk_score < 40)
            .scalar()
            or 0
        )
        medium_risk = (
            db.query(func.count(TransactionModel.id))
            .filter(TransactionModel.risk_score.between(40, 69.9))
            .scalar()
            or 0
        )
        high_risk_count = high_risk  # already calculated

        # Simple Anomaly Detection (risk > 85)
        anomalies = (
            db.query(func.count(TransactionModel.id))
            .filter(TransactionModel.risk_score > 85)
            .scalar()
            or 0
        )

        return TransactionStatsResponse(
            total_transactions=total_tx,
            total_amount=float(total_amount),
            avg_amount=float(avg_amount),
            max_amount=float(max_amount),
            min_amount=float(min_amount),
            avg_risk_score=float(avg_risk),
            high_risk_count=high_risk,
            status_distribution=status_dist,
            currency_distribution=currency_dist,
            risk_distribution=RiskDistribution(
                low=low_risk, medium=medium_risk, high=high_risk_count
            ),
            anomalies_count=anomalies,
        )

    except Exception as e:
        logger.error("Stats calculation failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
