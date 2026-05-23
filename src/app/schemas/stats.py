from pydantic import BaseModel
from typing import Dict


class RiskDistribution(BaseModel):
    low: int  # risk < 40
    medium: int  # 40 <= risk < 70
    high: int  # risk >= 70


class TransactionStatsResponse(BaseModel):
    total_transactions: int
    total_amount: float
    avg_amount: float
    max_amount: float
    min_amount: float
    avg_risk_score: float
    high_risk_count: int
    status_distribution: Dict[str, int]
    currency_distribution: Dict[str, int]
    risk_distribution: RiskDistribution
    anomalies_count: int
    period: str = "all_time"
