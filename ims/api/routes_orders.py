"""Order processing routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..api.dependencies import get_session
from ..api.utils import map_service_error
from ..models import Order
from ..schemas import (
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
    OutstandingOrderBalanceRead,
    PaymentCreate,
    PaymentRead,
)
from ..services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(
    customer_id: int | None = None, session: Session = Depends(get_session)
) -> list[OrderRead]:
    service = OrderService(session)
    return service.list_orders(customer_id=customer_id)


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, session: Session = Depends(get_session)) -> OrderRead:
    service = OrderService(session)
    try:
        order = service.create_order(
            customer_id=payload.customer_id,
            items=[(item.item_id, item.quantity) for item in payload.items],
            notes=payload.notes,
            status=payload.status,
        )
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return order


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, session: Session = Depends(get_session)) -> OrderRead:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.put("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int, payload: OrderStatusUpdate, session: Session = Depends(get_session)
) -> OrderRead:
    service = OrderService(session)
    try:
        order = service.update_status(order_id, payload.status)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return order


@router.post("/{order_id}/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def record_payment(
    order_id: int, payload: PaymentCreate, session: Session = Depends(get_session)
) -> PaymentRead:
    service = OrderService(session)
    try:
        payment = service.record_payment(order_id, payload.amount, payload.method)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return payment


@router.get("/{order_id}/balance", response_model=OutstandingOrderBalanceRead)
def order_balance(order_id: int, session: Session = Depends(get_session)) -> OutstandingOrderBalanceRead:
    service = OrderService(session)
    try:
        balance = service.outstanding_balance(order_id)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    return OutstandingOrderBalanceRead(order_id=order_id, outstanding_balance=balance)


