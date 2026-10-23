from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commerce import InventoryMovement, User
from app.schemas.commerce import InventoryAdjustment, MovementRead
from app.security import current_user
from app.services.inventory import locked_products, move_stock

router = APIRouter(prefix="/inventory", tags=["Inventory"], dependencies=[Depends(current_user)])


@router.get("/movements", response_model=list[MovementRead])
def list_movements(product_id: int | None = Query(None, gt=0),
                   offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                   db: Session = Depends(get_db)):
    query = select(InventoryMovement)
    if product_id is not None:
        query = query.where(InventoryMovement.product_id == product_id)
    return db.scalars(query.order_by(InventoryMovement.id.desc()).offset(offset).limit(limit)).all()


@router.post("/adjustments", response_model=MovementRead, status_code=201)
def adjust_inventory(data: InventoryAdjustment, db: Session = Depends(get_db),
                     user: User = Depends(current_user)):
    product = locked_products(db, [data.product_id])[data.product_id]
    if not product.active:
        raise HTTPException(404, "Product not found")
    movement = move_stock(db, product, data.quantity, data.reason, user.id)
    db.commit()
    db.refresh(movement)
    return movement
