import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# IMPORTANTE:
# cargamos las variables de testing ANTES de importar nuestra aplicación
test_env_path = Path(".env.test")
if not test_env_path.is_file():
    raise RuntimeError(
        "No se pueden ejecutar las pruebas: falta el archivo .env.test. "
        "Se cancela para evitar operaciones destructivas en otra base de datos."
    )

load_dotenv(test_env_path, override=True)

if os.getenv("DB_NAME") != "orderflow_test_db":
    raise RuntimeError(
        "No se pueden ejecutar las pruebas: DB_NAME debe ser exactamente "
        "'orderflow_test_db'. Se cancela para proteger la base de desarrollo."
    )

from app.database import Base, get_db
from app.main import app
from app.models.products import Product  # registra el modelo en Base.metadata


test_database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)


test_engine = create_engine(
    test_database_url,
    pool_pre_ping=True,
)


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
)


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
