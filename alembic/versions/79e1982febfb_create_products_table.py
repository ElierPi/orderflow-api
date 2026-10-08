"""create products table

Revision ID: 79e1982febfb
Revises: 4016cab05e0d
Create Date: 2026-10-08 08:16:26.228526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79e1982febfb'
down_revision: Union[str, Sequence[str], None] = '4016cab05e0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
