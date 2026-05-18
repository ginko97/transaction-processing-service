from fastapi.testclient import TestClient

# Use absolute import from installed package
from app.main import app  # ← Change from src.app.main

client = TestClient(app)


def test_validate_transaction_approved():
    response = client.post(
        "/transactions/validate",
        json={
            "amount": 1250.75,
            "currency": "USD",
            "merchant_id": "MERCH001",
            "customer_id": "CUST123",
            "description": "Test",
            "card_last4": "4242",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["approved", "review", "declined"]
    assert "transaction_id" in data
    assert 0 <= data["risk_score"] <= 100
