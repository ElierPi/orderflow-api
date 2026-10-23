"""Fail closed before opening a test connection; never inherit shell/.env values."""
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL

TEST_DATABASE = "orderflow_test_db"


def test_database_url(path: Path) -> URL:
    if not path.is_file():
        raise RuntimeError("Database tests require a complete .env.test file.")
    values = dotenv_values(path, interpolate=False)
    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    if any(values.get(key) is None for key in required):
        raise RuntimeError("Incomplete test configuration; no environment fallback allowed.")
    if any(not values[key].strip() for key in required if key != "DB_PASSWORD"):
        raise RuntimeError("Test connection settings must not be empty.")
    if values["DB_NAME"] != TEST_DATABASE:
        raise RuntimeError("Database tests require exactly orderflow_test_db.")
    try:
        port = int(values["DB_PORT"])
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise RuntimeError("Invalid test database port.") from None
    return URL.create(
        "postgresql+psycopg", username=values["DB_USER"],
        password=values["DB_PASSWORD"], host=values["DB_HOST"],
        port=port, database=TEST_DATABASE,
    )


def assert_test_database(connection) -> None:
    from sqlalchemy import text
    actual = connection.execute(text("SELECT current_database()")).scalar_one()
    if actual != TEST_DATABASE:
        raise RuntimeError("Connected database is not orderflow_test_db; refusing DDL.")
