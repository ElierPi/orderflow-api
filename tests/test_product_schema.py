from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.products import ProductCreate


def test_create_valid_product():
    product = ProductCreate(
        name="Mechanical Keyboard",
        price=Decimal("250000.00"),
        stock=10,
    )

    assert product.name == "Mechanical Keyboard"
    assert product.price == Decimal("250000.00")
    assert product.stock == 10


def test_product_rejects_negative_price():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Mechanical Keyboard",
            price=Decimal("-500.00"),
            stock=10,
        )


def test_product_rejects_negative_stock():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Mechanical Keyboard",
            price=Decimal("250000.00"),
            stock=-1,
        )