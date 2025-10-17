"""Customer management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..api.dependencies import get_session
from ..api.utils import map_service_error
from ..models import Customer
from ..schemas import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    LoyaltyAdjustment,
    OutstandingBalanceRead,
)
from ..services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=list[CustomerRead])
def list_customers(session: Session = Depends(get_session)) -> list[CustomerRead]:
    service = CustomerService(session)
    return service.list_customers()


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, session: Session = Depends(get_session)) -> CustomerRead:
    service = CustomerService(session)
    customer = service.create_customer(**payload.model_dump())
    session.flush()
    return customer


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, session: Session = Depends(get_session)) -> CustomerRead:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, payload: CustomerUpdate, session: Session = Depends(get_session)) -> CustomerRead:
    service = CustomerService(session)
    try:
        customer = service.update_customer(customer_id, **payload.model_dump(exclude_unset=True))
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, session: Session = Depends(get_session)) -> None:
    service = CustomerService(session)
    try:
        service.delete_customer(customer_id)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error


@router.get("/{customer_id}/balance", response_model=OutstandingBalanceRead)
def customer_outstanding_balance(customer_id: int, session: Session = Depends(get_session)) -> OutstandingBalanceRead:
    service = CustomerService(session)
    balance = service.outstanding_payments(customer_id)
    return OutstandingBalanceRead(customer_id=customer_id, outstanding_balance=balance)


@router.post("/{customer_id}/loyalty/add", response_model=CustomerRead)
def add_loyalty_points(
    customer_id: int, payload: LoyaltyAdjustment, session: Session = Depends(get_session)
) -> CustomerRead:
    service = CustomerService(session)
    try:
        customer = service.add_loyalty_points(customer_id, payload.points)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return customer


@router.post("/{customer_id}/loyalty/redeem", response_model=CustomerRead)
def redeem_loyalty_points(
    customer_id: int, payload: LoyaltyAdjustment, session: Session = Depends(get_session)
) -> CustomerRead:
    service = CustomerService(session)
    try:
        customer = service.redeem_loyalty_points(customer_id, payload.points)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return customer


