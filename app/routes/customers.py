from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commerce import Customer
from app.schemas.commerce import CustomerRead, CustomerWrite
from app.security import administrator, current_user

router = APIRouter(prefix="/customers", tags=["Customers"], dependencies=[Depends(current_user)])


def save(db, customer):
    db.add(customer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Customer email already exists") from None
    db.refresh(customer)
    return customer


def find(db, customer_id, lock=False):
    query = select(Customer).where(Customer.id == customer_id, Customer.active.is_(True))
    if lock:
        query = query.with_for_update()
    customer = db.scalar(query)
    if customer is None:
        raise HTTPException(404, "Customer not found")
    return customer


@router.post("/", response_model=CustomerRead, status_code=201)
def create_customer(data: CustomerWrite, db: Session = Depends(get_db)):
    return save(db, Customer(**data.model_dump()))


@router.get("/", response_model=list[CustomerRead])
def list_customers(q: str | None = Query(None, max_length=100), offset: int = Query(0, ge=0),
                   limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    query = select(Customer).where(Customer.active.is_(True))
    if q:
        pattern = f"%{q}%"
        query = query.where(Customer.name.ilike(pattern) | Customer.email.ilike(pattern))
    return db.scalars(query.order_by(Customer.id).offset(offset).limit(limit)).all()


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return find(db, customer_id)


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, data: CustomerWrite, db: Session = Depends(get_db)):
    customer = find(db, customer_id, lock=True)
    for key, value in data.model_dump().items():
        setattr(customer, key, value)
    return save(db, customer)


@router.delete("/{customer_id}", status_code=204, dependencies=[Depends(administrator)])
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = find(db, customer_id, lock=True)
    customer.active = False
    db.commit()
    return Response(status_code=204)
