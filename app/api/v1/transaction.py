from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from uuid import uuid4
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from ...schemas.transaction import (
    TransactionValidateRequest,
    TransactionValidateResponse,
    ErrorResponse,
)
from ...schemas.transaction import TransactionPredictResponse
from ...schemas.stats import TransactionStatsResponse, RiskDistribution
from ...core.logger import logger
from ...core.database import get_db, SessionLocal
from ...models.transaction import TransactionModel
from ...ml.features.feature_engineering import create_features
from ...core.rules import calculate_risk_score
from ...ml.models.fraud_model import train_fraud_model

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_model(request: Request):
    return getattr(request.app.state, "model", None)


@router.post("/predict", response_model=TransactionPredictResponse)
async def predict_fraud(
    request: TransactionValidateRequest,
    db: Session = Depends(get_db),
    model=Depends(get_model),
):
    """Real-time fraud prediction using XGBoost model."""
    try:
        logger.info("Fraud prediction request", extra={"amount": str(request.amount)})

        # Calculate rule-based risk score for accurate ML prediction features
        calculated_risk = calculate_risk_score(
            amount=request.amount,
            currency=request.currency,
            card_last4=request.card_last4,
        )

        # Create single row for prediction
        df = pd.DataFrame(
            [
                {
                    "amount": request.amount,
                    "currency": request.currency,
                    "merchant_id": request.merchant_id,
                    "customer_id": request.customer_id,
                    "risk_score": calculated_risk,
                }
            ]
        )

        df = create_features(df)

        feature_cols = [
            "amount",
            "amount_log",
            "risk_score",
            "risk_score_scaled",
            "tx_count_customer",
            "avg_amount_customer",
            "amount_vs_avg_customer",
            "hour",
            "is_night",
            "high_amount_flag",
            "high_risk_flag",
        ]

        X = df[feature_cols]

        if model is not None:
            fraud_prob = model.predict_proba(X)[0][1]
            is_fraud = fraud_prob > 0.5
        else:
            # Fallback
            fraud_prob = 0.3 if request.amount < 5000 else 0.75
            is_fraud = fraud_prob > 0.5

        recommendation = "BLOCK" if is_fraud else "APPROVE"

        response = TransactionPredictResponse(
            transaction_id=str(uuid4()),
            predicted_fraud=is_fraud,
            fraud_probability=round(float(fraud_prob), 4),
            risk_score=calculated_risk,
            recommendation=recommendation,
        )

        logger.info(
            "Prediction completed",
            extra={"fraud_probability": fraud_prob, "recommendation": recommendation},
        )
        return response

    except Exception as e:
        logger.error("Prediction failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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

        # Risk scoring logic using central rules engine
        risk_score = calculate_risk_score(
            amount=request.amount,
            currency=request.currency,
            card_last4=request.card_last4,
        )

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
        # Query basic aggregates in a single database round-trip using conditional aggregation
        aggregates = db.query(
            func.count(TransactionModel.id).label("total_tx"),
            func.sum(TransactionModel.amount).label("total_amount"),
            func.avg(TransactionModel.amount).label("avg_amount"),
            func.max(TransactionModel.amount).label("max_amount"),
            func.min(TransactionModel.amount).label("min_amount"),
            func.avg(TransactionModel.risk_score).label("avg_risk"),
            func.sum(case((TransactionModel.risk_score >= 70, 1), else_=0)).label(
                "high_risk"
            ),
            func.sum(case((TransactionModel.risk_score < 40, 1), else_=0)).label(
                "low_risk"
            ),
            func.sum(
                case((TransactionModel.risk_score.between(40, 69.9), 1), else_=0)
            ).label("medium_risk"),
            func.sum(case((TransactionModel.risk_score > 85, 1), else_=0)).label(
                "anomalies"
            ),
        ).first()

        total_tx = aggregates.total_tx or 0
        total_amount = aggregates.total_amount or 0.0
        avg_amount = aggregates.avg_amount or 0.0
        max_amount = aggregates.max_amount or 0.0
        min_amount = aggregates.min_amount or 0.0
        avg_risk = aggregates.avg_risk or 0.0
        high_risk = int(aggregates.high_risk or 0)
        low_risk = int(aggregates.low_risk or 0)
        medium_risk = int(aggregates.medium_risk or 0)
        anomalies = int(aggregates.anomalies or 0)

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
                low=low_risk, medium=medium_risk, high=high_risk
            ),
            anomalies_count=anomalies,
        )

    except Exception as e:
        logger.error("Stats calculation failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def trigger_training(
    background_tasks: BackgroundTasks,
    request: Request,
):
    """Asynchronously train the XGBoost model on the database records."""

    def run_training():
        db_session = SessionLocal()
        try:
            logger.info("Starting background fraud model training...")
            trained_model = train_fraud_model(db_session)
            if trained_model is not None:
                request.app.state.model = trained_model
                logger.info("Successfully retrained and hot-reloaded the fraud model")
            else:
                logger.warning(
                    "Retraining finished but no model was returned (insufficient data)"
                )
        except Exception:
            logger.error("Background fraud model training failed", exc_info=True)
        finally:
            db_session.close()

    background_tasks.add_task(run_training)
    return {"message": "Model training triggered successfully in the background."}
