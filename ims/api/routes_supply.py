"""Supply chain automation routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..api.dependencies import get_session
from ..api.utils import map_service_error
from ..schemas import (
    AutoReorderRequest,
    AutoReorderResponse,
    PurchaseOrderCreate,
    PurchaseOrderRead,
    ShipmentCreate,
    ShipmentRead,
)
from ..services.supply_service import SupplyService

router = APIRouter(prefix="/supply", tags=["Supply"])


@router.get("/purchase-orders", response_model=list[PurchaseOrderRead])
def list_purchase_orders(
    supplier_id: int | None = None,
    session: Session = Depends(get_session),
) -> list[PurchaseOrderRead]:
    service = SupplyService(session)
    return service.list_purchase_orders(supplier_id=supplier_id)


@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreate, session: Session = Depends(get_session)
) -> PurchaseOrderRead:
    service = SupplyService(session)
    try:
        purchase_order = service.create_purchase_order(
            supplier_id=payload.supplier_id,
            items=[(line.item_id, line.quantity, line.unit_cost) for line in payload.items],
            expected_date=payload.expected_date,
        )
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return purchase_order


@router.post("/shipments", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED)
def receive_shipment(payload: ShipmentCreate, session: Session = Depends(get_session)) -> ShipmentRead:
    service = SupplyService(session)
    try:
        shipment = service.receive_shipment(
            purchase_order_id=payload.purchase_order_id,
            received_by=payload.received_by,
            received_lines=[(line.item_id, line.quantity) for line in payload.received_lines],
            received_date=payload.received_date,
            notes=payload.notes,
        )
    except ValueError as error:  # pragma: no cover - converted to HTTP response
        raise map_service_error(error) from error
    session.flush()
    return shipment


@router.get("/shipments", response_model=list[ShipmentRead])
def list_shipments(session: Session = Depends(get_session)) -> list[ShipmentRead]:
    service = SupplyService(session)
    return service.inbound_shipments()


@router.get("/expected", response_model=list[PurchaseOrderRead])
def expected_receipts(session: Session = Depends(get_session)) -> list[PurchaseOrderRead]:
    service = SupplyService(session)
    return service.expected_receipts()


@router.post("/auto-reorder", response_model=AutoReorderResponse)
def auto_reorder(
    payload: AutoReorderRequest, session: Session = Depends(get_session)
) -> AutoReorderResponse:
    service = SupplyService(session)
    purchase_orders = service.auto_reorder(minimum_quantity=payload.minimum_quantity)
    session.flush()
    return AutoReorderResponse(created_orders=[po.id for po in purchase_orders])


