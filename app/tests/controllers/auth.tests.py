from fastapi.testclient import TestClient


def test_signup_201(client: TestClient):
    resp = client.post("/api/auth/signup", json={
        "email": "user@test.com", "username": "testuser", "password": "password123",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "user@test.com"
    assert "jwt_token" in body
    assert "id" in body


def test_signup_409_duplicate_email(client: TestClient):
    payload = {"email": "dup@test.com", "username": "u", "password": "password123"}
    client.post("/api/auth/signup", json=payload)
    resp = client.post("/api/auth/signup", json=payload)
    assert resp.status_code == 409


def test_signup_422_invalid_email(client: TestClient):
    resp = client.post("/api/auth/signup", json={
        "email": "not-an-email", "username": "u", "password": "password123",
    })
    assert resp.status_code == 422


def test_signup_422_short_password(client: TestClient):
    resp = client.post("/api/auth/signup", json={
        "email": "ok@test.com", "username": "u", "password": "short",
    })
    assert resp.status_code == 422


def test_signin_200(client: TestClient):
    client.post("/api/auth/signup", json={
        "email": "login@test.com", "username": "u", "password": "password123",
    })
    resp = client.post("/api/auth/signin", json={
        "email": "login@test.com", "password": "password123",
    })
    assert resp.status_code == 200
    assert "jwt_token" in resp.json()


def test_signin_401_wrong_password(client: TestClient):
    client.post("/api/auth/signup", json={
        "email": "wp@test.com", "username": "u", "password": "password123",
    })
    resp = client.post("/api/auth/signin", json={
        "email": "wp@test.com", "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_signin_401_unknown_email(client: TestClient):
    resp = client.post("/api/auth/signin", json={
        "email": "nobody@test.com", "password": "password123",
    })
    assert resp.status_code == 401
