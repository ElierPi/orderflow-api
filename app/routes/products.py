from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.products import Product
from app.schemas.products import (
    ProductCreate,
    ProductResponse,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    new_product = Product(
        name=product.name,
        price=product.price,
        stock=product.stock,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get(
    "/",
    response_model=list[ProductResponse],
)
def get_products(
    db: Session = Depends(get_db),
):
    result = db.scalars(
        select(Product).order_by(Product.id)
    )

    return result.all()