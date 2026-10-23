import pytest


def test_create_product(client):
    response = client.post(
        "/products/",
        json={
            "name": "Mechanical Keyboard",
            "description": "Hot-swappable switches",
            "price": "250000.00",
            "stock": 10,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Mechanical Keyboard"
    assert data["description"] == "Hot-swappable switches"
    assert client.get(f"/products/{data['id']}").json()["description"] == data["description"]
    assert data["price"] == "250000.00"
    assert data["stock"] == 10
    assert "id" in data

def test_get_products(client):
    client.post(
        "/products/",
        json={
            "name": "Mouse Gamer",
            "price": "120000.00",
            "stock": 5,
        },
    )

    response = client.get("/products/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Mouse Gamer"
    assert data[0]["price"] == "120000.00"
    assert data[0]["stock"] == 5


def test_get_product_by_id(client):
    create_response = client.post(
        "/products/",
        json={
            "name": "Monitor 24",
            "price": "650000.00",
            "stock": 3,
        },
    )

    product_id = create_response.json()["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Monitor 24"
    assert data["price"] == "650000.00"
    assert data["stock"] == 3




    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Monitor 24"
    assert data["price"] == "650000.00"
    assert data["stock"] == 3


def test_get_nonexistent_product_returns_404(client):
    response = client.get(
        "/products/999999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Product not found"
    }

def test_update_product(client):
    create_response = client.post(
        "/products/",
        json={
            "name": "Keyboard Basic",
            "price": "150000.00",
            "stock": 5,
        },
    )

    product_id = create_response.json()["id"]

    response = client.put(
        f"/products/{product_id}",
        json={
            "name": "Keyboard Pro",
            "description": "Wireless keyboard",
            "price": "250000.00",
            "stock": 12,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Keyboard Pro"
    assert data["description"] == "Wireless keyboard"
    assert client.get(f"/products/{product_id}").json()["description"] == "Wireless keyboard"
    assert data["price"] == "250000.00"
    assert data["stock"] == 12

def test_update_nonexistent_product_returns_404(client):
    response = client.put(
        "/products/999999",
        json={
            "name": "Ghost Product",
            "price": "100000.00",
            "stock": 1,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Product not found"
    }

def test_delete_product(client):
    create_response = client.post(
        "/products/",
        json={
            "name": "Mouse Temporal",
            "price": "90000.00",
            "stock": 4,
        },
    )

    product_id = create_response.json()["id"]

    response = client.delete(
        f"/products/{product_id}"
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/products/{product_id}"
    )

    assert get_response.status_code == 404

def test_delete_nonexistent_product_returns_404(client):
    response = client.delete(
        "/products/999999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Product not found"
    }


@pytest.mark.parametrize("replacement", [None, "Updated description"])
def test_replace_product_description(client, replacement):
    payload = dict(name="Keyboard", description="Original", price="10.00", stock=2)
    product_id = client.post("/products/", json=payload).json()["id"]
    payload["description"] = replacement
    assert client.put(f"/products/{product_id}", json=payload).status_code == 200
    assert client.get(f"/products/{product_id}").json()["description"] == replacement


def test_put_omitted_description_clears_it(client):
    payload = dict(name="Keyboard", price="10.00", stock=2)
    product_id = client.post("/products/", json={**payload, "description": "Original"}).json()["id"]
    assert client.put(f"/products/{product_id}", json=payload).status_code == 200
    assert client.get(f"/products/{product_id}").json()["description"] is None
