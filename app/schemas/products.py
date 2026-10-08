from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    description: str | None = Field(
        default=None,
        max_length=255
    )

    price: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )

    stock: int = Field(ge=0)


class ProductResponse(ProductCreate):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )