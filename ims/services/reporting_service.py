"""Reporting and analytics helpers."""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from io import StringIO
from typing import Iterable, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import (
    Item,
    Order,
    OrderItem,
    PurchaseOrder,
    Shipment,
    Supplier,
)


@dataclass
class SalesSummary:
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal


@dataclass
class InventoryStatus:
    sku: str
    name: str
    stock_quantity: int
    reorder_level: int


class ReportingService:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    @property
    def session(self) -> Session:
        if self._external_session is None:
            raise RuntimeError("Session is only available within context manager")
        return self._external_session

    def __enter__(self) -> "ReportingService":
        if self._external_session is None:
            self._manager = session_scope()
            self._external_session = self._manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self, "_manager"):
            self._manager.__exit__(exc_type, exc, tb)
            self._external_session = None

    def sales_summary(self) -> SalesSummary:
        total_orders = self.session.scalar(select(func.count(Order.id))) or 0
        total_revenue = self.session.scalar(select(func.sum(Order.total))) or Decimal("0.00")
        average = total_revenue / total_orders if total_orders else Decimal("0.00")
        return SalesSummary(total_orders=total_orders, total_revenue=total_revenue, average_order_value=average)

    def inventory_status(self) -> list[InventoryStatus]:
        items = self.session.scalars(select(Item))
        return [
            InventoryStatus(sku=item.sku, name=item.name, stock_quantity=item.stock_quantity, reorder_level=item.reorder_level)
            for item in items
        ]

    def supplier_performance(self) -> dict[int, dict[str, float]]:
        performance: dict[int, dict[str, float]] = defaultdict(lambda: {"on_time_rate": 0.0, "orders": 0})
        shipments = self.session.scalars(select(Shipment))
        counts: dict[int, int] = defaultdict(int)
        on_time_counts: dict[int, int] = defaultdict(int)
        for shipment in shipments:
            supplier_id = shipment.purchase_order.supplier_id
            counts[supplier_id] += 1
            if shipment.on_time:
                on_time_counts[supplier_id] += 1
        for supplier_id, count in counts.items():
            performance[supplier_id]["on_time_rate"] = on_time_counts[supplier_id] / count if count else 0.0
            performance[supplier_id]["orders"] = count
        return performance

    def export_inventory_csv(self) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["SKU", "Name", "Quantity", "Reorder Level"])
        for status in self.inventory_status():
            writer.writerow([status.sku, status.name, status.stock_quantity, status.reorder_level])
        return output.getvalue()

    def sales_trends(self) -> dict[str, Decimal]:
        stmt = (
            select(func.strftime("%Y-%m", Order.created_at), func.sum(Order.total))
            .group_by(func.strftime("%Y-%m", Order.created_at))
            .order_by(func.strftime("%Y-%m", Order.created_at))
        )
        return {row[0]: row[1] for row in self.session.execute(stmt)}


__all__ = ["ReportingService", "SalesSummary", "InventoryStatus"]
