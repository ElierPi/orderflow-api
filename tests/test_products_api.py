def test_create_product(client):
    response = client.post(
        "/products/",
        json={
            "name": "Mechanical Keyboard",
            "price": "250000.00",
            "stock": 10,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Mechanical Keyboard"
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
            "price": "250000.00",
            "stock": 12,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Keyboard Pro"
    assert data["price"] == "250000.00"
    assert data["stock"] == 12