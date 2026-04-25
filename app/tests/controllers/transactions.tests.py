from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.utils.enum.transaction import TransactionStatus


def _seed_user(session: Session) -> User:
    user = User(email="tx@test.com", username="txuser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# GET /{user_id}/balance

def test_get_balance_200(client: TestClient, test_session: Session):
    _seed_user(test_session)
    with patch(
        "music_genre_sommelier.models.transaction.Transaction.get_balance",
        return_value=150.0,
    ):
        resp = client.get("/api/transactions/1/balance")
    assert resp.status_code == 200
    assert resp.json() == {"balance": 150.0}


def test_get_balance_403_other_user(client: TestClient):
    resp = client.get("/api/transactions/2/balance")
    assert resp.status_code == 403


def test_get_balance_404_user_not_found(client: TestClient):
    resp = client.get("/api/transactions/1/balance")
    assert resp.status_code == 404


# GET /{user_id}

def test_list_transactions_200(client: TestClient, test_session: Session):
    user = _seed_user(test_session)
    test_session.add(Transaction(user_id=user.id, amount=50.0, status=TransactionStatus.SUCCESS))
    test_session.commit()

    resp = client.get("/api/transactions/1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_transactions_403_other_user(client: TestClient):
    resp = client.get("/api/transactions/2")
    assert resp.status_code == 403


def test_list_transactions_404_user_not_found(client: TestClient):
    resp = client.get("/api/transactions/1")
    assert resp.status_code == 404


# POST /{user_id}/funds

def test_add_funds_201(client: TestClient, test_session: Session):
    _seed_user(test_session)
    resp = client.post("/api/transactions/1/funds", json={"amount": 100.0})
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 100.0
    assert data["status"] == TransactionStatus.SUCCESS


def test_add_funds_403_other_user(client: TestClient):
    resp = client.post("/api/transactions/2/funds", json={"amount": 100.0})
    assert resp.status_code == 403


def test_add_funds_404_user_not_found(client: TestClient):
    resp = client.post("/api/transactions/1/funds", json={"amount": 100.0})
    assert resp.status_code == 404


def test_add_funds_422_negative_amount(client: TestClient):
    resp = client.post("/api/transactions/1/funds", json={"amount": -10.0})
    assert resp.status_code == 422


def test_add_funds_422_zero_amount(client: TestClient):
    resp = client.post("/api/transactions/1/funds", json={"amount": 0.0})
    assert resp.status_code == 422
