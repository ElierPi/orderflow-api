import os
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commerce import User

hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)
# Equalize the expensive password verification for unknown accounts.
dummy_hash = hasher.hash("not-a-real-account-password")


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32 or secret.startswith("replace_"):
        raise HTTPException(503, "Configure a private JWT_SECRET of at least 32 characters.")
    return secret


def verify_password(password: str, encoded: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def issue_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "iat": now, "exp": now + timedelta(minutes=30),
         "iss": "orderflow", "aud": "orderflow-api"},
        jwt_secret(), algorithm="HS256",
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(401, "Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    try:
        claims = jwt.decode(
            credentials.credentials, jwt_secret(), algorithms=["HS256"],
            audience="orderflow-api", issuer="orderflow",
            options={"require": ["sub", "exp", "iat", "iss", "aud"]},
        )
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise unauthorized from None
    user = db.get(User, user_id)
    if user is None or not user.active:
        raise unauthorized
    return user


def administrator(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Administrator permission required")
    return user
