from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models.commerce import Customer, InventoryMovement, Order
from app.models.products import Product


@pytest.fixture()
def catalog(client):
    customer = client.post("/customers/", json={"name": "Ada Lovelace", "email": "ada@example.com"}).json()
    products = [client.post("/products/", json={"name": name, "description": "Office equipment",
                "price": price, "stock": stock}).json()
                for name, price, stock in [("Keyboard", "19.99", 10), ("Monitor", "100.00", 2)]]
    return customer, products


def order_payload(catalog):
    customer, products = catalog
    return {"customer_id": customer["id"], "items": [{"product_id": p["id"], "quantity": 2} for p in products]}


def test_product_search_filters_and_pagination(client, catalog):
    assert len(client.get("/products/?q=office").json()) == 2
    assert client.get("/products/?q=KEYboard").json()[0]["name"] == "Keyboard"
    assert len(client.get("/products/?min_price=20&max_price=150&in_stock=true").json()) == 1
    assert len(client.get("/products/?offset=1&limit=1").json()) == 1
    assert client.get("/products/?offset=100").json() == []


@pytest.mark.parametrize("query", ["limit=101", "limit=0", "offset=-1", "min_price=10&max_price=1"])
def test_invalid_product_filters(client, query):
    assert client.get("/products/?" + query).status_code == 422


@pytest.mark.parametrize("field,value", [("name", "  "), ("price", "0"), ("price", "1.234"),
                                         ("stock", -1), ("stock", 2147483648), ("description", "x" * 256)])
def test_invalid_product_never_persisted(client, field, value, db):
    payload = dict(name="Keyboard", price="12.00", stock=10)
    payload[field] = value
    assert client.post("/products/", json=payload).status_code == 422
    assert db.scalar(select(func.count()).select_from(Product)) == 0


def test_customer_crud_and_safe_delete(client, catalog, db):
    customer_id = catalog[0]["id"]
    assert client.get(f"/customers/{customer_id}").status_code == 200
    response = client.put(f"/customers/{customer_id}", json={"name": "Ada Updated", "email": "ADA@example.com", "phone": "123"})
    assert response.json()["email"] == "ada@example.com"
    assert len(client.get("/customers/?q=Updated&limit=1").json()) == 1
    order = client.post("/orders/", json=order_payload(catalog)).json()
    assert client.delete(f"/customers/{customer_id}").status_code == 204
    assert client.get(f"/customers/{customer_id}").status_code == 404
    assert client.get(f"/orders/{order['id']}").status_code == 200
    assert db.get(Customer, customer_id).active is False
    assert client.post("/orders/", json=order_payload(catalog)).status_code == 404


def test_customer_duplicate_and_validation(client, catalog):
    assert client.post("/customers/", json={"name": "Duplicate", "email": "ADA@example.com"}).status_code == 409
    assert client.post("/customers/", json={"name": "Missing email"}).status_code == 422
    assert client.post("/customers/", json={"name": "Bad email", "email": "invalid"}).status_code == 422
    assert client.get("/customers/999999").status_code == 404


def test_order_totals_inventory_snapshot_and_history(client, catalog, db):
    response = client.post("/orders/", json=order_payload(catalog))
    assert response.status_code == 201, response.text
    order = response.json()
    assert order["total"] == "239.98"
    assert order["items"][0]["subtotal"] == "39.98"
    assert order["status"] == "pending"
    assert [client.get(f"/products/{p['id']}").json()["stock"] for p in catalog[1]] == [8, 0]
    movements = db.scalars(select(InventoryMovement).where(InventoryMovement.order_id == order["id"])).all()
    assert len(movements) == 2
    assert all(m.quantity == -2 and m.actor_id for m in movements)
    first = catalog[1][0]
    client.put(f"/products/{first['id']}", json={"name": "New name", "price": "50.00", "stock": 8})
    persisted = client.get(f"/orders/{order['id']}").json()
    assert persisted["items"][0]["unit_price"] == "19.99"
    assert persisted["items"][0]["product_name"] == "Keyboard"
    assert len(client.get(f"/orders/?customer_id={catalog[0]['id']}&status=pending").json()) == 1


def test_failed_order_is_atomic(client, catalog, db):
    payload = order_payload(catalog)
    payload["items"][1]["quantity"] = 3
    before = db.scalar(select(func.count()).select_from(InventoryMovement))
    assert client.post("/orders/", json=payload).status_code == 409
    assert db.scalar(select(func.count()).select_from(Order)) == 0
    assert db.scalar(select(func.count()).select_from(InventoryMovement)) == before
    assert [p.stock for p in db.scalars(select(Product).order_by(Product.id))] == [10, 2]


def test_cancel_restores_stock_exactly_once_and_preserves_archived_product(client, catalog):
    order = client.post("/orders/", json=order_payload(catalog)).json()
    product_id = catalog[1][0]["id"]
    assert client.delete(f"/products/{product_id}").status_code == 204
    response = client.patch(f"/orders/{order['id']}/status", json={"status": "cancelled"})
    assert response.status_code == 200
    assert client.patch(f"/orders/{order['id']}/status", json={"status": "cancelled"}).status_code == 409
    movements = client.get(f"/inventory/movements?product_id={product_id}").json()
    assert movements[0]["stock_after"] == 10
    assert movements[0]["reason"] == "Order cancellation"


def test_order_state_machine(client, catalog):
    order_id = client.post("/orders/", json=order_payload(catalog)).json()["id"]
    url = f"/orders/{order_id}/status"
    assert client.patch(url, json={"status": "shipped"}).status_code == 409
    assert client.patch(url, json={"status": "confirmed"}).status_code == 200
    assert client.patch(url, json={"status": "shipped"}).status_code == 200
    assert client.patch(url, json={"status": "cancelled"}).status_code == 409
    assert client.patch("/orders/99999/status", json={"status": "confirmed"}).status_code == 404


def test_invalid_order_lines_and_missing_references(client, catalog):
    payload = order_payload(catalog)
    payload["items"].append(payload["items"][0])
    assert client.post("/orders/", json=payload).status_code == 422
    assert client.post("/orders/", json={"customer_id": catalog[0]["id"], "items": []}).status_code == 422
    payload = order_payload(catalog)
    payload["items"][0]["quantity"] = 0
    assert client.post("/orders/", json=payload).status_code == 422
    payload["items"][0] = {"product_id": 999999, "quantity": 1}
    assert client.post("/orders/", json=payload).status_code == 404


def test_inventory_adjustments_are_audited(client, catalog, db):
    product_id = catalog[1][0]["id"]
    for quantity, stock in [(5, 15), (-3, 12)]:
        response = client.post("/inventory/adjustments", json={"product_id": product_id, "quantity": quantity, "reason": "Warehouse count"})
        assert response.status_code == 201
        assert response.json()["stock_after"] == stock
        assert response.json()["actor_id"] is not None
    assert client.post("/inventory/adjustments", json={"product_id": product_id, "quantity": -13, "reason": "Cannot oversell"}).status_code == 409
    assert db.get(Product, product_id).stock == 12
    assert client.post("/inventory/adjustments", json={"product_id": product_id, "quantity": 0, "reason": "No change"}).status_code == 422
    assert len(client.get(f"/inventory/movements?product_id={product_id}").json()) == 3


def test_database_enforces_stock_constraint(db):
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(Product(name="Invalid", price=Decimal("1.00"), stock=-1))
        db.flush()


def test_dashboard_uses_real_totals_and_excludes_cancelled(client, catalog):
    order = client.post("/orders/", json=order_payload(catalog)).json()
    stats = client.get("/dashboard/")
    assert stats.status_code == 200
    data = stats.json()
    assert data["products"] == 2
    assert data["customers"] == 1
    assert data["orders"] == data["pending_orders"] == 1
    assert Decimal(data["order_value"]) == Decimal("239.98")
    assert len(data["daily_value"]) == 7
    assert sum(Decimal(day["total"]) for day in data["daily_value"]) == Decimal("239.98")
    client.patch(f"/orders/{order['id']}/status", json={"status": "cancelled"})
    assert Decimal(client.get("/dashboard/").json()["order_value"]) == 0
