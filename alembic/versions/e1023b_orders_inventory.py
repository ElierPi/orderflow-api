"""Add transactional orders, inventory audit, and product archival.

Revision ID: e1023b
Revises: e1023a
"""
from alembic import op
import sqlalchemy as sa

revision = "e1023b"
down_revision = "e1023a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("products", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table(
        "orders", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total", sa.Numeric(16, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'confirmed', 'shipped', 'cancelled')", name="ck_order_status"),
        sa.CheckConstraint("total > 0", name="ck_order_total"),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_table(
        "order_items", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_name", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(16, 2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_item_quantity"),
        sa.CheckConstraint("unit_price > 0 AND subtotal > 0", name="ck_item_price"),
    )
    for column in ("order_id", "product_id"):
        op.create_index(f"ix_order_items_{column}", "order_items", [column])
    op.create_table(
        "inventory_movements", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="RESTRICT")),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("stock_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity <> 0", name="ck_movement_quantity"),
        sa.CheckConstraint("stock_after >= 0", name="ck_movement_stock"),
    )
    for column in ("order_id", "product_id"):
        op.create_index(f"ix_inventory_movements_{column}", "inventory_movements", [column])
    # Preserve existing stock with a clearly labelled migration baseline.
    op.execute("""INSERT INTO inventory_movements (product_id, quantity, stock_after, reason)
                  SELECT id, stock, stock, 'Migration opening balance' FROM products WHERE stock > 0""")


def downgrade():
    op.drop_table("inventory_movements")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_column("products", "active")
