"""Inventory-related API routes."""
from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..models import Item
from ..services.inventory_service import InventoryService
from ..api.dependencies import get_session
from ..api.utils import map_service_error
from ..schemas import (
    BarcodeRead,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    InventoryTransactionRead,
    InventoryValuationRead,
    ItemCreate,
    ItemRead,
    ItemUpdate,
    LowStockAlertRead,
    StockAdjustment,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> list[CategoryRead]:
    service = InventoryService(session)
    return service.list_categories()


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, session: Session = Depends(get_session)) -> CategoryRead:
    service = InventoryService(session)
    category = service.create_category(name=payload.name, description=payload.description)
    session.flush()
    return category


@router.put("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, session: Session = Depends(get_session)) -> CategoryRead:
    service = InventoryService(session)
    try:
        category = service.update_category(category_id, **payload.model_dump(exclude_unset=True))
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, session: Session = Depends(get_session)) -> None:
    service = InventoryService(session)
    try:
        service.delete_category(category_id)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error


@router.get("/items", response_model=list[ItemRead])
def list_items(
    category_id: int | None = Query(default=None, description="Filter by category id"),
    session: Session = Depends(get_session),
) -> list[ItemRead]:
    service = InventoryService(session)
    return service.list_items(category_id=category_id)


@router.get("/items/{item_id}", response_model=ItemRead)
def get_item(item_id: int, session: Session = Depends(get_session)) -> ItemRead:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, session: Session = Depends(get_session)) -> ItemRead:
    service = InventoryService(session)
    item = service.create_item(**payload.model_dump())
    session.flush()
    return item


@router.put("/items/{item_id}", response_model=ItemRead)
def update_item(item_id: int, payload: ItemUpdate, session: Session = Depends(get_session)) -> ItemRead:
    service = InventoryService(session)
    try:
        item = service.update_item(item_id, **payload.model_dump(exclude_unset=True))
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, session: Session = Depends(get_session)) -> None:
    service = InventoryService(session)
    try:
        service.delete_item(item_id)
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error


@router.post("/items/{item_id}/adjust", response_model=InventoryTransactionRead)
def adjust_stock(item_id: int, payload: StockAdjustment, session: Session = Depends(get_session)) -> InventoryTransactionRead:
    service = InventoryService(session)
    try:
        transaction = service.adjust_stock(
            item_id=item_id,
            quantity_change=payload.quantity_change,
            reason=payload.reason,
            reference=payload.reference,
        )
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return transaction


@router.get("/alerts", response_model=list[LowStockAlertRead])
def low_stock_alerts(session: Session = Depends(get_session)) -> list[LowStockAlertRead]:
    service = InventoryService(session)
    return service.low_stock_alerts()


@router.get("/valuation", response_model=InventoryValuationRead)
def inventory_valuation(session: Session = Depends(get_session)) -> InventoryValuationRead:
    service = InventoryService(session)
    total = service.inventory_valuation()
    return InventoryValuationRead(total_value=total)


@router.get("/reorder", response_model=list[ItemRead])
def items_to_reorder(session: Session = Depends(get_session)) -> list[ItemRead]:
    service = InventoryService(session)
    return service.items_to_reorder()


@router.get("/items/{item_id}/barcode", response_model=BarcodeRead)
def item_barcode(item_id: int, session: Session = Depends(get_session)) -> BarcodeRead:
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    service = InventoryService(session)
    image = service.generate_barcode_image(item.sku)
    barcode_value = item.barcode or service.generate_barcode_value(item.sku)
    encoded_image = base64.b64encode(image).decode()
    return BarcodeRead(value=barcode_value, image_base64=encoded_image)


