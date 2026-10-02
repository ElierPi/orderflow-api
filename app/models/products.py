from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    stock: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    __table_args__ = (
        CheckConstraint("price > 0"),
        CheckConstraint("stock >= 0"),
    )