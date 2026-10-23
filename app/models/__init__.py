"""Register every mapped table, including for CLI and migration entry points."""
from app.models.products import Product
from app.models.commerce import Customer, InventoryMovement, Order, OrderItem, User

__all__ = ["Product", "Customer", "InventoryMovement", "Order", "OrderItem", "User"]
