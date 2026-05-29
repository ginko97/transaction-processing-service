from fastapi.testclient import TestClient
from app.main import app
from app.core.rules import calculate_risk_score

client = TestClient(app)


def test_calculate_risk_score():
    # USD, card_last4=4242 (which starts with 4), amount <= 5000:
    # Base 12 - 5 = 7
    assert calculate_risk_score(1000.0, "USD", "4242") == 7.0

    # Non-USD, amount > 10000:
    # Base 12, override to 82 (for amount > 10000) + 18 (Non-USD) = 100
    assert calculate_risk_score(15000.0, "EUR") == 100.0

    # USD, amount > 5000:
    # Base 12 + 35 = 47
    assert calculate_risk_score(6000.0, "USD") == 47.0


def test_validate_and_stats():
    # Insert multiple transactions using /validate and verify /stats computes aggregates correctly
    amounts = [2000.0, 6000.0, 15000.0]
    for amt in amounts:
        res = client.post(
            "/transactions/validate",
            json={
                "amount": amt,
                "currency": "EUR" if amt > 10000 else "USD",
                "merchant_id": "M1",
                "customer_id": "C1",
                "description": f"Amt {amt}",
            },
        )
        assert res.status_code == 200

    # Call /stats
    res = client.get("/transactions/stats")
    assert res.status_code == 200
    stats = res.json()

    assert stats["total_transactions"] >= 3
    assert stats["total_amount"] >= 23000.0
    assert stats["max_amount"] >= 15000.0
    assert stats["min_amount"] <= 2000.0
    assert stats["anomalies_count"] >= 1  # 15000.0 gets risk score 100.0 (> 85)


def test_predict_endpoint():
    res = client.post(
        "/transactions/predict",
        json={
            "amount": 2500.0,
            "currency": "USD",
            "merchant_id": "M1",
            "customer_id": "C1",
            "description": "Prediction test",
            "card_last4": "4242",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "predicted_fraud" in data
    assert "fraud_probability" in data
    # risk_score should be calculated risk (7.0 for USD 2500 with card 4242)
    assert data["risk_score"] == 7.0


def test_train_endpoint():
    # Trigger model training endpoint
    res = client.post("/transactions/train")
    assert res.status_code == 200
    data = res.json()
    assert "triggered" in data["message"]
