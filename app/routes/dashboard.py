from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commerce import Customer, Order
from app.models.products import Product
from app.schemas.products import ProductResponse
from app.security import current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(current_user)])


class DailyValue(BaseModel):
    date: str
    total: Decimal


class DashboardRead(BaseModel):
    products: int
    customers: int
    orders: int
    pending_orders: int
    order_value: Decimal
    low_stock: list[ProductResponse]
    daily_value: list[DailyValue]


@router.get("/", response_model=DashboardRead)
def dashboard(db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=6)
    utc_date = func.date(func.timezone("UTC", Order.created_at))
    totals = dict(db.execute(select(utc_date, func.sum(Order.total)).where(
        utc_date >= start, Order.status != "cancelled").group_by(utc_date)).all())
    return DashboardRead(
        products=db.scalar(select(func.count()).select_from(Product).where(Product.active.is_(True))),
        customers=db.scalar(select(func.count()).select_from(Customer).where(Customer.active.is_(True))),
        orders=db.scalar(select(func.count()).select_from(Order)),
        pending_orders=db.scalar(select(func.count()).select_from(Order).where(Order.status == "pending")),
        order_value=db.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(Order.status != "cancelled")),
        low_stock=db.scalars(select(Product).where(Product.active.is_(True), Product.stock <= 5)
                             .order_by(Product.stock, Product.id).limit(5)).all(),
        daily_value=[DailyValue(date=(start + timedelta(days=i)).isoformat(),
                               total=totals.get(start + timedelta(days=i), Decimal("0.00"))) for i in range(7)],
    )
