"""add description to products

Revision ID: d07f3a432009
Revises: 79e1982febfb
Create Date: 2026-10-08 08:27:26.477692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd07f3a432009'
down_revision: Union[str, Sequence[str], None] = '79e1982febfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "products",
        "description",
    )
