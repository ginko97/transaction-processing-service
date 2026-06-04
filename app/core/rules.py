import re
from typing import Optional
from decimal import Decimal


def calculate_risk_score(
    amount: float | Decimal, currency: str, card_last4: Optional[str] = None
) -> float:
    """Calculate rule-based risk score for a transaction.

    Returns a score between 0.0 and 100.0.
    """
    risk_score = 12.0
    amount_val = float(amount)
    if amount_val > 10000:
        risk_score = 82.0
    elif amount_val > 5000:
        risk_score += 35.0

    if currency != "USD":
        risk_score += 18.0

    if card_last4 and re.match(r"^4[0-9]{3}$", card_last4):
        risk_score -= 5.0

    return float(max(0.0, min(100.0, risk_score)))
