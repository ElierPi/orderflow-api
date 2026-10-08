"""create products table

Revision ID: 4016cab05e0d
Revises: 
Create Date: 2026-10-08 07:20:35.578549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4016cab05e0d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "price",
            sa.Numeric(12, 2),
            nullable=False,
        ),
        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "price > 0"
        ),
        sa.CheckConstraint(
            "stock >= 0"
        ),
    )


def downgrade() -> None:
    op.drop_table("products")