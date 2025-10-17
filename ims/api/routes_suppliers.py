"""Supplier management API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..api.dependencies import get_session
from ..api.utils import map_service_error
from ..models import Supplier
from ..schemas import (
    PurchaseOrderRead,
    SupplierBalanceRead,
    SupplierCreate,
    SupplierLinkItem,
    SupplierPerformanceRead,
    SupplierRead,
    SupplierUpdate,
)
from ..services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=list[SupplierRead])
def list_suppliers(session: Session = Depends(get_session)) -> list[SupplierRead]:
    service = SupplierService(session)
    return service.list_suppliers()


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, session: Session = Depends(get_session)) -> SupplierRead:
    service = SupplierService(session)
    supplier = service.create_supplier(**payload.model_dump())
    session.flush()
    return supplier


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, session: Session = Depends(get_session)) -> SupplierRead:
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierRead)
def update_supplier(supplier_id: int, payload: SupplierUpdate, session: Session = Depends(get_session)) -> SupplierRead:
    service = SupplierService(session)
    try:
        supplier = service.update_supplier(supplier_id, **payload.model_dump(exclude_unset=True))
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: int, session: Session = Depends(get_session)) -> None:
    service = SupplierService(session)
    try:
        service.delete_supplier(supplier_id)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error


@router.post("/{supplier_id}/items", response_model=SupplierRead)
def link_supplier_item(
    supplier_id: int,
    payload: SupplierLinkItem,
    session: Session = Depends(get_session),
) -> SupplierRead:
    service = SupplierService(session)
    try:
        supplier = service.link_item(supplier_id, payload.item_id)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return supplier


@router.get("/{supplier_id}/purchase-orders", response_model=list[PurchaseOrderRead])
def supplier_purchase_history(supplier_id: int, session: Session = Depends(get_session)) -> list[PurchaseOrderRead]:
    service = SupplierService(session)
    return service.purchase_history(supplier_id)


@router.get("/{supplier_id}/balance", response_model=SupplierBalanceRead)
def supplier_outstanding_balance(supplier_id: int, session: Session = Depends(get_session)) -> SupplierBalanceRead:
    service = SupplierService(session)
    balance = service.outstanding_balance(supplier_id)
    return SupplierBalanceRead(supplier_id=supplier_id, outstanding_balance=balance)


@router.get("/performance", response_model=list[SupplierPerformanceRead])
def supplier_performance(
    supplier_id: int | None = None,
    session: Session = Depends(get_session),
) -> list[SupplierPerformanceRead]:
    service = SupplierService(session)
    return service.performance_metrics(supplier_id=supplier_id)


