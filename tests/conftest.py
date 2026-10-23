from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from tests.db_safety import assert_test_database, test_database_url as build_test_url

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def test_engine():
    # Lazy: pure validation and health tests need no database.
    engine = create_engine(
        build_test_url(ROOT / ".env.test"), pool_pre_ping=True,
        hide_parameters=True, connect_args={"connect_timeout": 5},
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db(test_engine):
    # Route commits use savepoints; the generated schema is rolled back afterward.
    # Existing public tables are never touched, and no drop_all() is needed.
    with test_engine.connect() as connection:
        transaction = connection.begin()
        try:
            assert_test_database(connection)
            schema = "test_" + uuid4().hex
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            config = Config(str(ROOT / "alembic.ini"))
            config.set_main_option("script_location", str(ROOT / "alembic"))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session
        finally:
            transaction.rollback()


@pytest.fixture()
def anonymous_client(db):
    from app.database import get_db
    from app.main import app

    def override_get_db():
        yield db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.fixture(autouse=True)
def test_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "orderflow-tests-only-key-not-for-deployment-123456789")


@pytest.fixture(scope="session")
def password_hash():
    from app.security import hasher
    return hasher.hash("Testing-password-123")


@pytest.fixture()
def admin_user(db, password_hash):
    from app.models.commerce import User
    user = User(email="admin@example.com", password_hash=password_hash, role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def client(anonymous_client, admin_user):
    from app.security import issue_token
    anonymous_client.headers["Authorization"] = "Bearer " + issue_token(admin_user)
    return anonymous_client
