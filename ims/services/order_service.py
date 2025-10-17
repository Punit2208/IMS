"""Order and sales management services."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import Customer, Item, Order, OrderItem, Payment
from .inventory_service import InventoryService


class OrderService:
    TAX_RATE = Decimal("0.10")

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    @property
    def session(self) -> Session:
        if self._external_session is None:
            raise RuntimeError("Session is only available within context manager")
        return self._external_session

    def __enter__(self) -> "OrderService":
        if self._external_session is None:
            self._manager = session_scope()
            self._external_session = self._manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self, "_manager"):
            self._manager.__exit__(exc_type, exc, tb)
            self._external_session = None

    def create_order(
        self,
        customer_id: int,
        items: Iterable[tuple[int, int]],
        notes: Optional[str] = None,
        status: str = "pending",
    ) -> Order:
        customer = self.session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        order = Order(customer=customer, status=status, notes=notes)
        subtotal = Decimal("0.00")
        self.session.add(order)
        self.session.flush()
        with InventoryService(self.session) as inventory_service:
            for item_id, quantity in items:
                item = self.session.get(Item, item_id)
                if not item:
                    raise ValueError(f"Item {item_id} not found")
                if item.stock_quantity < quantity:
                    raise ValueError(f"Insufficient stock for {item.sku}")
                order_item = OrderItem(order=order, item=item, quantity=quantity, unit_price=item.unit_price)
                subtotal += item.unit_price * quantity
                inventory_service.adjust_stock(item_id, -quantity, reason="order", reference=f"order:{order.id}")
        order.subtotal = subtotal
        order.tax = subtotal * self.TAX_RATE
        order.total = order.subtotal + order.tax
        return order

    def update_status(self, order_id: int, status: str) -> Order:
        order = self.session.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")
        order.status = status
        return order

    def list_orders(self, customer_id: Optional[int] = None) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc())
        if customer_id:
            stmt = stmt.where(Order.customer_id == customer_id)
        return list(self.session.scalars(stmt))

    def record_payment(self, order_id: int, amount: Decimal, method: str) -> Payment:
        order = self.session.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")
        payment = Payment(order=order, amount=amount, method=method, received_date=dt.datetime.utcnow())
        self.session.add(payment)
        return payment

    def outstanding_balance(self, order_id: int) -> Decimal:
        order = self.session.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")
        paid = sum(payment.amount for payment in order.payments)
        return order.total - paid


__all__ = ["OrderService"]
