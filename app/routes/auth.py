from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commerce import User
from app.schemas.commerce import Login, Registration, Token, UserRead
from app.security import current_user, dummy_hash, hasher, issue_token, jwt_secret, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(data: Registration, db: Session = Depends(get_db)):
    # Clients cannot choose their role; administrators are provisioned locally.
    user = User(email=data.email, password_hash=hasher.hash(data.password), role="operator")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered") from None
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    jwt_secret()
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    valid = verify_password(data.password, user.password_hash if user else dummy_hash)
    if not valid or user is None or not user.active:
        raise HTTPException(401, "Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=issue_token(user))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user
