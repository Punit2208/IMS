"""Customer management services."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import Customer, Order, Payment


class CustomerService:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    @property
    def session(self) -> Session:
        if self._external_session is None:
            raise RuntimeError("Session is only available within context manager")
        return self._external_session

    def __enter__(self) -> "CustomerService":
        if self._external_session is None:
            self._manager = session_scope()
            self._external_session = self._manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self, "_manager"):
            self._manager.__exit__(exc_type, exc, tb)
            self._external_session = None

    def create_customer(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        preferences: Optional[str] = None,
    ) -> Customer:
        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address,
            preferences=preferences,
        )
        self.session.add(customer)
        return customer

    def update_customer(self, customer_id: int, **kwargs) -> Customer:
        customer = self.session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)
        return customer

    def delete_customer(self, customer_id: int) -> None:
        customer = self.session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        self.session.delete(customer)

    def list_customers(self) -> list[Customer]:
        return list(self.session.scalars(select(Customer).order_by(Customer.name)))

    def outstanding_payments(self, customer_id: int) -> Decimal:
        total_stmt = select(func.sum(Order.total)).where(Order.customer_id == customer_id)
        total = self.session.scalar(total_stmt) or Decimal("0.00")
        paid_stmt = (
            select(func.sum(Payment.amount))
            .join(Order, Payment.order_id == Order.id)
            .where(Order.customer_id == customer_id)
        )
        paid = self.session.scalar(paid_stmt) or Decimal("0.00")
        return total - paid

    def add_loyalty_points(self, customer_id: int, points: int) -> Customer:
        customer = self.session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        customer.loyalty_points += points
        return customer

    def redeem_loyalty_points(self, customer_id: int, points: int) -> Customer:
        customer = self.session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        if customer.loyalty_points < points:
            raise ValueError("Insufficient loyalty points")
        customer.loyalty_points -= points
        return customer


__all__ = ["CustomerService"]
