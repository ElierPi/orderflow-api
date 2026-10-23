"""Real concurrent connections in a disposable, uniquely named PostgreSQL schema."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session

from app.models.commerce import Customer, InventoryMovement, Order, User
from app.models.products import Product
from app.routes.orders import change_status, create_order
from app.schemas.commerce import OrderCreate, OrderStatusChange
from tests.conftest import ROOT
from tests.db_safety import assert_test_database


@pytest.fixture()
def concurrent_schema(test_engine, password_hash):
    # Concurrent sessions need committed DDL. Only this fixture's generated schema
    # is dropped; existing schemas and tables are never altered.
    schema = "test_concurrent_" + uuid4().hex
    with test_engine.begin() as connection:
        assert_test_database(connection)
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        config = Config(str(ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(ROOT / "alembic"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    try:
        def session_factory():
            session = Session(test_engine)
            @event.listens_for(session, "after_begin")
            def isolate_every_transaction(_session, _transaction, connection):
                connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                connection.execute(text("SET LOCAL lock_timeout = '5s'"))
            return session

        with session_factory() as db:
            user = User(email="concurrent@example.com", password_hash=password_hash, role="admin")
            customers = [Customer(name=f"Customer {i}", email=f"c{i}@example.com") for i in range(2)]
            product = Product(name="Last keyboard", price="10.00", stock=1)
            db.add_all([user, product, *customers])
            db.flush()
            ids = (user.id, product.id, [customer.id for customer in customers])
            db.commit()
        yield session_factory, ids
    finally:
        with test_engine.begin() as connection:
            assert_test_database(connection)
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


def test_concurrent_orders_cannot_oversell(concurrent_schema):
    session_factory, (user_id, product_id, customers) = concurrent_schema
    barrier = Barrier(2)

    def worker(customer_id):
        with session_factory() as db:
            user = db.get(User, user_id)
            barrier.wait(timeout=5)
            try:
                create_order(OrderCreate(customer_id=customer_id, items=[{"product_id": product_id, "quantity": 1}]), db, user)
                return 201
            except HTTPException as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(worker, customers))
    assert sorted(results) == [201, 409]
    with session_factory() as db:
        assert db.get(Product, product_id).stock == 0
        assert db.scalar(select(func.count()).select_from(Order)) == 1
        assert db.scalar(select(func.count()).select_from(InventoryMovement)) == 1


def test_concurrent_cancellations_restore_stock_once(concurrent_schema):
    session_factory, (user_id, product_id, customers) = concurrent_schema
    with session_factory() as db:
        order = create_order(OrderCreate(customer_id=customers[0], items=[{"product_id": product_id, "quantity": 1}]), db, db.get(User, user_id))
        order_id = order.id
    barrier = Barrier(2)

    def worker(_):
        with session_factory() as db:
            user = db.get(User, user_id)
            barrier.wait(timeout=5)
            try:
                change_status(order_id, OrderStatusChange(status="cancelled"), db, user)
                return 200
            except HTTPException as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(worker, range(2)))
    assert sorted(results) == [200, 409]
    with session_factory() as db:
        assert db.get(Product, product_id).stock == 1
        assert db.scalar(select(func.count()).select_from(InventoryMovement)) == 2
