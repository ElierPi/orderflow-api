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