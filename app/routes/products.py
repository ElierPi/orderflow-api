from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.products import Product
from app.models.commerce import User
from app.security import administrator, current_user
from app.services.inventory import locked_products, move_stock
from app.schemas.products import (
    ProductCreate,
    ProductResponse,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(current_user)],
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(administrator),
):
    new_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=0,
    )

    db.add(new_product)
    db.flush()
    if product.stock:
        move_stock(db, new_product, product.stock, "Initial stock", user.id)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get(
    "/",
    response_model=list[ProductResponse],
)
def get_products(
    q: str | None = Query(None, max_length=100),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    in_stock: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(422, "min_price must not exceed max_price")
    query = select(Product).where(Product.active.is_(True))
    if q:
        query = query.where(Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%"))
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if in_stock is not None:
        query = query.where(Product.stock > 0 if in_stock else Product.stock == 0)
    result = db.scalars(query.order_by(Product.id).offset(offset).limit(limit))

    return result.all()

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None or not product.active:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product

@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    data: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(administrator),
):
    product = locked_products(db, [product_id])[product_id]

    if not product.active:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    product.name = data.name
    product.description = data.description
    product.price = data.price
    if data.stock != product.stock:
        move_stock(db, product, data.stock - product.stock, "Product stock update", user.id)

    db.commit()
    db.refresh(product)

    return product

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(administrator),
):
    product = locked_products(db, [product_id])[product_id]

    if not product.active:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    # Preserve order references and the inventory audit trail.
    product.active = False
    db.commit()
