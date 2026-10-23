from fastapi import HTTPException
from sqlalchemy import select

from app.models.commerce import InventoryMovement
from app.models.products import Product


def locked_products(db, ids):
    # All stock writers acquire row locks in ID order to avoid lock-order cycles.
    products = db.scalars(select(Product).where(Product.id.in_(ids)).order_by(Product.id).with_for_update()).all()
    if len(products) != len(set(ids)):
        raise HTTPException(404, "Product not found")
    return {product.id: product for product in products}


def move_stock(db, product, quantity, reason, actor_id, order_id=None):
    stock = product.stock + quantity
    if not 0 <= stock <= 2_147_483_647:
        raise HTTPException(409, "Insufficient stock or stock limit exceeded")
    product.stock = stock
    movement = InventoryMovement(product_id=product.id, order_id=order_id, actor_id=actor_id,
                                 quantity=quantity, stock_after=stock, reason=reason)
    db.add(movement)
    return movement
