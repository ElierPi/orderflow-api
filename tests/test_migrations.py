from uuid import uuid4

from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text

from app.database import Base
from tests.conftest import ROOT
from tests.db_safety import assert_test_database


def test_upgrade_preserves_existing_catalog_and_records_opening_stock(test_engine):
    with test_engine.connect() as connection:
        transaction = connection.begin()
        try:
            assert_test_database(connection)
            schema = "test_upgrade_" + uuid4().hex
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            config = Config(str(ROOT / "alembic.ini"))
            config.set_main_option("script_location", str(ROOT / "alembic"))
            config.attributes["connection"] = connection
            command.upgrade(config, "d07f3a432009")
            connection.execute(text("""INSERT INTO products (name, description, price, stock)
                                      VALUES ('Existing keyboard', 'Preserve me', 12.34, 7)"""))
            command.upgrade(config, "head")
            product = connection.execute(text("SELECT name, description, stock, active FROM products")).one()
            assert tuple(product) == ("Existing keyboard", "Preserve me", 7, True)
            movement = connection.execute(text("SELECT quantity, stock_after, reason FROM inventory_movements")).one()
            assert tuple(movement) == (7, 7, "Migration opening balance")
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
        finally:
            transaction.rollback()
