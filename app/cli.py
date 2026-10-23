"""Local administrator provisioning: python -m app.cli --email you@example.com."""
import argparse
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models.commerce import User
from app.schemas.commerce import Registration
from app.security import hasher


def main():
    parser = argparse.ArgumentParser(description="Provision one OrderFlow administrator")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass("Password (12+ characters): ")
    if password != getpass("Repeat password: "):
        raise SystemExit("Passwords do not match.")
    try:
        data = Registration(email=args.email, password=password)
    except ValueError:
        raise SystemExit("Invalid email or password length (12–128 characters).") from None
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == data.email)):
            raise SystemExit("Account already exists; no changes made.")
        db.add(User(email=data.email, password_hash=hasher.hash(password), role="admin"))
        db.commit()
    print("Administrator created.")


if __name__ == "__main__":
    main()
