from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commerce import Customer, Order, OrderItem, User
from app.schemas.commerce import OrderCreate, OrderRead, OrderStatusChange
from app.security import current_user
from app.services.inventory import locked_products, move_stock

router = APIRouter(prefix="/orders", tags=["Orders"], dependencies=[Depends(current_user)])


@router.post("/", response_model=OrderRead, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = db.scalar(select(Customer).where(Customer.id == data.customer_id).with_for_update())
    if customer is None or not customer.active:
        raise HTTPException(404, "Customer not found")
    products = locked_products(db, [item.product_id for item in data.items])
    total = Decimal("0.00")
    lines = []
    # Validate ALL lines before mutating anything.
    for item in data.items:
        product = products[item.product_id]
        if not product.active:
            raise HTTPException(404, "Product not found")
        if product.stock < item.quantity:
            raise HTTPException(409, f"Insufficient stock for product {product.id}")
        subtotal = product.price * item.quantity
        total += subtotal
        lines.append(OrderItem(product_id=product.id, product_name=product.name,
                               quantity=item.quantity, unit_price=product.price, subtotal=subtotal))
    if total >= Decimal("100000000000000"):
        raise HTTPException(422, "Order total exceeds the supported limit")
    order = Order(customer_id=customer.id, total=total, items=lines, status="pending")
    db.add(order)
    db.flush()
    for item in data.items:
        move_stock(db, products[item.product_id], -item.quantity, "Order reservation", user.id, order.id)
    db.commit()
    db.refresh(order)
    return order


@router.get("/", response_model=list[OrderRead])
def list_orders(customer_id: int | None = Query(None, gt=0),
                status: Literal["pending", "confirmed", "shipped", "cancelled"] | None = None,
                offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                db: Session = Depends(get_db)):
    query = select(Order)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    if status:
        query = query.where(Order.status == status)
    return db.scalars(query.order_by(Order.id.desc()).offset(offset).limit(limit)).all()


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderRead)
def change_status(order_id: int, data: OrderStatusChange, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if order is None:
        raise HTTPException(404, "Order not found")
    transitions = {"pending": {"confirmed", "cancelled"}, "confirmed": {"shipped", "cancelled"}}
    if data.status not in transitions.get(order.status, set()):
        raise HTTPException(409, "Invalid order status transition")
    if data.status == "cancelled":
        products = locked_products(db, [item.product_id for item in order.items])
        # Validate every restored quantity before changing any line.
        if any(products[item.product_id].stock + item.quantity > 2_147_483_647 for item in order.items):
            raise HTTPException(409, "Restored stock would exceed the supported limit")
        for item in order.items:
            move_stock(db, products[item.product_id], item.quantity, "Order cancellation", user.id, order.id)
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
