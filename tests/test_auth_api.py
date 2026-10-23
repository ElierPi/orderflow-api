from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.models.commerce import User
from app.security import jwt_secret, verify_password


def test_registration_hashes_password_and_cannot_escalate(anonymous_client, db):
    payload = {"email": "Operator@example.com", "password": "Long-password-123", "role": "admin"}
    response = anonymous_client.post("/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["role"] == "operator"
    assert "password" not in response.text
    user = db.scalar(select(User).where(User.email == "operator@example.com"))
    assert user.password_hash != payload["password"]
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(payload["password"], user.password_hash)
    assert anonymous_client.post("/auth/register", json=payload).status_code == 409


def test_login_me_and_operator_permissions(anonymous_client, admin_user):
    login = anonymous_client.post("/auth/login", json={"email": admin_user.email, "password": "Testing-password-123"})
    assert login.status_code == 200
    anonymous_client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
    assert anonymous_client.get("/auth/me").json()["role"] == "admin"
    anonymous_client.post("/auth/register", json={"email": "op@example.com", "password": "Operator-password-123"})
    token = anonymous_client.post("/auth/login", json={"email": "op@example.com", "password": "Operator-password-123"}).json()["access_token"]
    anonymous_client.headers["Authorization"] = "Bearer " + token
    assert anonymous_client.get("/products/").status_code == 200
    assert anonymous_client.post("/products/", json={"name": "Keyboard", "price": "1", "stock": 2}).status_code == 403
    assert anonymous_client.delete("/customers/1").status_code == 403
    assert anonymous_client.post("/customers/", json={"name": "Customer", "email": "customer@example.com"}).status_code == 201


@pytest.mark.parametrize("path", ["/products/", "/customers/", "/orders/", "/inventory/movements", "/auth/me"])
def test_private_endpoints_require_token(anonymous_client, path):
    assert anonymous_client.get(path).status_code == 401


def test_bad_login_and_inactive_account(anonymous_client, admin_user, db):
    for email in ["missing@example.com", admin_user.email]:
        assert anonymous_client.post("/auth/login", json={"email": email, "password": "wrong"}).status_code == 401
    admin_user.active = False
    db.commit()
    assert anonymous_client.post("/auth/login", json={"email": admin_user.email, "password": "Testing-password-123"}).status_code == 401


@pytest.mark.parametrize("kind", ["expired", "forged", "wrong_audience", "missing_exp", "malformed"])
def test_invalid_jwt_rejected(anonymous_client, admin_user, kind):
    now = datetime.now(timezone.utc)
    claims = {"sub": str(admin_user.id), "iat": now, "exp": now + timedelta(minutes=5), "iss": "orderflow", "aud": "orderflow-api"}
    secret = jwt_secret()
    if kind == "expired":
        claims["exp"] = now - timedelta(minutes=1)
    elif kind == "forged":
        secret = "different-signing-key-for-tests-only-123456789"
    elif kind == "wrong_audience":
        claims["aud"] = "another-service"
    elif kind == "missing_exp":
        del claims["exp"]
    token = "bad-token" if kind == "malformed" else jwt.encode(claims, secret, algorithm="HS256")
    assert anonymous_client.get("/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_login_fails_closed_without_secret(anonymous_client, monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    assert anonymous_client.post("/auth/login", json={"email": "x@example.com", "password": "anything"}).status_code == 503


def test_validation_response_never_echoes_password(anonymous_client):
    response = anonymous_client.post("/auth/register", json={"email": "valid@example.com", "password": "S3cr3t!"})
    assert response.status_code == 422
    assert "S3cr3t!" not in response.text
    assert "input" not in response.json()["detail"][0]
