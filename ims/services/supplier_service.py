"""Supplier management services."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import PurchaseOrder, Supplier


@dataclass
class SupplierPerformance:
    supplier_id: int
    company_name: str
    on_time_rate: float
    average_delivery_days: Optional[float]
    total_orders: int
    accuracy_rate: Optional[float]


class SupplierService:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    @property
    def session(self) -> Session:
        if self._external_session is None:
            raise RuntimeError("Session is only available within context manager")
        return self._external_session

    def __enter__(self) -> "SupplierService":
        if self._external_session is None:
            self._manager = session_scope()
            self._external_session = self._manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self, "_manager"):
            self._manager.__exit__(exc_type, exc, tb)
            self._external_session = None

    def create_supplier(
        self,
        company_name: str,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        address: Optional[str] = None,
        payment_terms: Optional[str] = None,
    ) -> Supplier:
        supplier = Supplier(
            company_name=company_name,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            address=address,
            payment_terms=payment_terms,
        )
        self.session.add(supplier)
        return supplier

    def update_supplier(self, supplier_id: int, **kwargs) -> Supplier:
        supplier = self.session.get(Supplier, supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")
        for key, value in kwargs.items():
            if hasattr(supplier, key) and value is not None:
                setattr(supplier, key, value)
        return supplier

    def list_suppliers(self) -> list[Supplier]:
        return list(self.session.scalars(select(Supplier).order_by(Supplier.company_name)))

    def delete_supplier(self, supplier_id: int) -> None:
        supplier = self.session.get(Supplier, supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")
        self.session.delete(supplier)

    def link_item(self, supplier_id: int, item_id: int) -> Supplier:
        supplier = self.session.get(Supplier, supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")
        from ..models import Item  # local import to avoid circular dependency

        item = self.session.get(Item, item_id)
        if not item:
            raise ValueError("Item not found")
        if item not in supplier.items:
            supplier.items.append(item)
        return supplier

    def purchase_history(self, supplier_id: int) -> list[PurchaseOrder]:
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.supplier_id == supplier_id)
            .order_by(PurchaseOrder.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def outstanding_balance(self, supplier_id: int) -> Decimal:
        stmt = select(func.sum(PurchaseOrder.total_cost)).where(
            PurchaseOrder.supplier_id == supplier_id, PurchaseOrder.status != "received"
        )
        result: Optional[Decimal] = self.session.scalar(stmt)
        return result or Decimal("0.00")

    def performance_metrics(self, supplier_id: Optional[int] = None) -> list[SupplierPerformance]:
        stmt = select(Supplier)
        if supplier_id:
            stmt = stmt.where(Supplier.id == supplier_id)
        suppliers = list(self.session.scalars(stmt))
        metrics: list[SupplierPerformance] = []
        for supplier in suppliers:
            on_time_count = 0
            total_shipments = 0
            delivery_days: list[int] = []
            order_accuracy: list[float] = []
            for po in supplier.purchase_orders:
                for receipt in po.receipts:
                    total_shipments += 1
                    if receipt.on_time:
                        on_time_count += 1
                    if receipt.received_date and po.expected_date:
                        delta = receipt.received_date.date() - po.expected_date
                        delivery_days.append(delta.days)
                # accuracy: compare ordered vs received quantities
                ordered_qty = sum(line.quantity for line in po.lines)
                received_qty = sum(line.quantity for line in po.lines)  # placeholder: assume perfect
                if ordered_qty:
                    order_accuracy.append(received_qty / ordered_qty)
            metrics.append(
                SupplierPerformance(
                    supplier_id=supplier.id,
                    company_name=supplier.company_name,
                    on_time_rate=(on_time_count / total_shipments) if total_shipments else 0.0,
                    average_delivery_days=(sum(delivery_days) / len(delivery_days)) if delivery_days else None,
                    total_orders=len(supplier.purchase_orders),
                    accuracy_rate=(sum(order_accuracy) / len(order_accuracy)) if order_accuracy else None,
                )
            )
        return metrics


__all__ = ["SupplierService", "SupplierPerformance"]
