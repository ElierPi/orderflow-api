from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class CustomerWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=254)
    phone: str | None = Field(default=None, max_length=30)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


class CustomerRead(CustomerWrite):
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: bool


class Registration(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: Literal["admin", "operator"]
    active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrderLine(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1_000_000)


class OrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    items: list[OrderLine] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def distinct_products(self):
        ids = [item.product_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Each product must appear once; combine its quantities.")
        return self


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    status: str
    total: Decimal
    created_at: datetime
    items: list[OrderItemRead]


class OrderStatusChange(BaseModel):
    status: Literal["confirmed", "shipped", "cancelled"]


class InventoryAdjustment(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=-1_000_000, le=1_000_000)
    reason: str = Field(min_length=3, max_length=255)

    @field_validator("quantity")
    @classmethod
    def nonzero(cls, value):
        if value == 0:
            raise ValueError("Quantity must be nonzero.")
        return value


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    order_id: int | None
    actor_id: int | None
    quantity: int
    stock_after: int
    reason: str
    created_at: datetime
