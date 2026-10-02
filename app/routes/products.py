from fastapi import APIRouter
from app.schemas.products import ProductCreate

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post("/")
def create_product(product: ProductCreate):
    return {
        "message": "Product created successfully",
        "product": product
    }