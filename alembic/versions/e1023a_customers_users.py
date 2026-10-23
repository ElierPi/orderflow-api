"""Add customers and authenticated users.

Revision ID: e1023a
Revises: d07f3a432009
"""
from alembic import op
import sqlalchemy as sa

revision = "e1023a"
down_revision = "d07f3a432009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customers", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "users", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="operator"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("role IN ('admin', 'operator')", name="ck_user_role"),
    )


def downgrade():
    op.drop_table("users")
    op.drop_table("customers")
