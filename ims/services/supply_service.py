"""Supply management services including purchase orders and shipments."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import Item, PurchaseOrder, PurchaseOrderLine, Shipment, Supplier
from .inventory_service import InventoryService


class SupplyService:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    @property
    def session(self) -> Session:
        if self._external_session is None:
            raise RuntimeError("Session is only available within context manager")
        return self._external_session

    def __enter__(self) -> "SupplyService":
        if self._external_session is None:
            self._manager = session_scope()
            self._external_session = self._manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self, "_manager"):
            self._manager.__exit__(exc_type, exc, tb)
            self._external_session = None

    def create_purchase_order(
        self,
        supplier_id: int,
        items: Iterable[tuple[int, int, Decimal]],
        expected_date: Optional[dt.date] = None,
    ) -> PurchaseOrder:
        supplier = self.session.get(Supplier, supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")
        purchase_order = PurchaseOrder(supplier=supplier, expected_date=expected_date, status="ordered")
        total_cost = Decimal("0.00")
        for item_id, quantity, unit_cost in items:
            item = self.session.get(Item, item_id)
            if not item:
                raise ValueError(f"Item {item_id} not found")
            line = PurchaseOrderLine(purchase_order=purchase_order, item=item, quantity=quantity, unit_cost=unit_cost)
            total_cost += unit_cost * quantity
        purchase_order.total_cost = total_cost
        self.session.add(purchase_order)
        return purchase_order

    def list_purchase_orders(self, supplier_id: Optional[int] = None) -> list[PurchaseOrder]:
        stmt = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
        if supplier_id:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
        return list(self.session.scalars(stmt))

    def receive_shipment(
        self,
        purchase_order_id: int,
        received_by: str,
        received_lines: Iterable[tuple[int, int]],
        received_date: Optional[dt.datetime] = None,
        notes: Optional[str] = None,
    ) -> Shipment:
        purchase_order = self.session.get(PurchaseOrder, purchase_order_id)
        if not purchase_order:
            raise ValueError("Purchase order not found")
        if received_date is None:
            received_date = dt.datetime.utcnow()
        shipment = Shipment(
            purchase_order=purchase_order,
            received_date=received_date,
            received_by=received_by,
            notes=notes,
            on_time=(purchase_order.expected_date is None)
            or (received_date.date() <= purchase_order.expected_date),
        )
        with InventoryService(self.session) as inventory_service:
            for item_id, quantity in received_lines:
                inventory_service.adjust_stock(item_id, quantity, reason="shipment", reference=f"po:{purchase_order_id}")
        remaining = sum(line.quantity for line in purchase_order.lines)
        if remaining <= sum(rl[1] for rl in received_lines):
            purchase_order.status = "received"
        self.session.add(shipment)
        return shipment

    def inbound_shipments(self) -> list[Shipment]:
        stmt = select(Shipment).order_by(Shipment.received_date.desc())
        return list(self.session.scalars(stmt))

    def expected_receipts(self) -> list[PurchaseOrder]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.status == "ordered")
        return list(self.session.scalars(stmt))

    def auto_reorder(self, minimum_quantity: int = 1) -> list[PurchaseOrder]:
        """Create purchase orders for items below their reorder level."""
        created_orders: list[PurchaseOrder] = []
        with InventoryService(self.session) as inventory_service:
            items = inventory_service.items_to_reorder()
        supplier_groups: dict[int, list[tuple[int, int, Decimal]]] = {}
        for item in items:
            if not item.suppliers:
                continue
            supplier = item.suppliers[0]
            quantity = max(item.reorder_level * 2 - item.stock_quantity, minimum_quantity)
            supplier_groups.setdefault(supplier.id, []).append((item.id, quantity, item.unit_price))
        for supplier_id, lines in supplier_groups.items():
            po = self.create_purchase_order(supplier_id=supplier_id, items=lines)
            created_orders.append(po)
        return created_orders


__all__ = ["SupplyService"]
