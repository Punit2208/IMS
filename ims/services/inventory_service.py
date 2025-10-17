"""Inventory and category management services."""
from __future__ import annotations

import io
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import qrcode
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import Category, Item, InventoryTransaction


@dataclass
class LowStockAlert:
    sku: str
    name: str
    quantity: int
    reorder_level: int


class InventoryService:
    """Service providing inventory-related operations."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    @property
    def session(self) -> Session:
        if self._external_session is None:
            raise RuntimeError("Session is only available within context manager")
        return self._external_session

    def __enter__(self) -> "InventoryService":
        if self._external_session is None:
            self._session_manager = session_scope()
            self._external_session = self._session_manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self, "_session_manager"):
            self._session_manager.__exit__(exc_type, exc, tb)
            self._external_session = None

    # Category operations
    def create_category(self, name: str, description: Optional[str] = None) -> Category:
        category = Category(name=name, description=description)
        self.session.add(category)
        return category

    def list_categories(self) -> list[Category]:
        return list(self.session.scalars(select(Category).order_by(Category.name)))

    def update_category(self, category_id: int, **kwargs) -> Category:
        category = self.session.get(Category, category_id)
        if not category:
            raise ValueError("Category not found")
        for key, value in kwargs.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)
        return category

    def delete_category(self, category_id: int) -> None:
        category = self.session.get(Category, category_id)
        if not category:
            raise ValueError("Category not found")
        self.session.delete(category)

    # Item operations
    def create_item(
        self,
        sku: str,
        name: str,
        unit_price: Decimal,
        category_id: Optional[int] = None,
        description: Optional[str] = None,
        unit: str = "unit",
        stock_quantity: int = 0,
        reorder_level: int = 0,
        image_path: Optional[str] = None,
    ) -> Item:
        item = Item(
            sku=sku,
            name=name,
            unit_price=unit_price,
            category_id=category_id,
            description=description,
            unit=unit,
            stock_quantity=stock_quantity,
            reorder_level=reorder_level,
            image_path=image_path,
        )
        item.barcode = self.generate_barcode_value(sku)
        self.session.add(item)
        self._record_transaction(item, stock_quantity, "initial stock", reference="init")
        return item

    def update_item(self, item_id: int, **kwargs) -> Item:
        item = self.session.get(Item, item_id)
        if not item:
            raise ValueError("Item not found")
        for key, value in kwargs.items():
            if key == "stock_quantity" and value is not None:
                delta = int(value) - item.stock_quantity
                if delta:
                    self.adjust_stock(item_id, delta, reason="manual update")
                continue
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        return item

    def delete_item(self, item_id: int) -> None:
        item = self.session.get(Item, item_id)
        if not item:
            raise ValueError("Item not found")
        self.session.delete(item)

    def list_items(self, category_id: Optional[int] = None) -> list[Item]:
        stmt = select(Item).order_by(Item.name)
        if category_id:
            stmt = stmt.where(Item.category_id == category_id)
        return list(self.session.scalars(stmt))

    def adjust_stock(self, item_id: int, quantity_change: int, reason: str, reference: Optional[str] = None) -> InventoryTransaction:
        item = self.session.get(Item, item_id)
        if not item:
            raise ValueError("Item not found")
        item.stock_quantity += quantity_change
        tx = self._record_transaction(item, quantity_change, reason, reference)
        return tx

    def _record_transaction(
        self,
        item: Item,
        change: int,
        reason: str,
        reference: Optional[str] = None,
    ) -> InventoryTransaction:
        tx = InventoryTransaction(item=item, change=change, reason=reason, reference=reference)
        self.session.add(tx)
        return tx

    def generate_barcode_value(self, sku: str) -> str:
        return f"SKU-{sku}"

    def generate_barcode_image(self, sku: str) -> bytes:
        barcode_value = self.generate_barcode_value(sku)
        img = qrcode.make(barcode_value)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def low_stock_alerts(self) -> list[LowStockAlert]:
        stmt = select(Item).where(Item.stock_quantity <= Item.reorder_level)
        items = self.session.scalars(stmt)
        return [
            LowStockAlert(sku=i.sku, name=i.name, quantity=i.stock_quantity, reorder_level=i.reorder_level)
            for i in items
        ]

    def items_to_reorder(self) -> list[Item]:
        stmt = select(Item).where(Item.stock_quantity <= Item.reorder_level)
        return list(self.session.scalars(stmt))

    def inventory_valuation(self) -> Decimal:
        stmt = select(func.sum(Item.unit_price * Item.stock_quantity))
        result: Optional[Decimal] = self.session.scalar(stmt)
        return result or Decimal("0.00")


__all__ = ["InventoryService", "LowStockAlert"]
