"""Reporting and analytics routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..api.dependencies import get_session
from ..schemas import InventoryStatusRead, SalesSummaryRead, SalesTrendRead
from ..services.reporting_service import ReportingService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/sales-summary", response_model=SalesSummaryRead)
def sales_summary(session: Session = Depends(get_session)) -> SalesSummaryRead:
    service = ReportingService(session)
    return service.sales_summary()


@router.get("/inventory-status", response_model=list[InventoryStatusRead])
def inventory_status(session: Session = Depends(get_session)) -> list[InventoryStatusRead]:
    service = ReportingService(session)
    return service.inventory_status()


@router.get("/sales-trends", response_model=list[SalesTrendRead])
def sales_trends(session: Session = Depends(get_session)) -> list[SalesTrendRead]:
    service = ReportingService(session)
    trends = service.sales_trends()
    return [SalesTrendRead(period=period, total=total) for period, total in trends.items()]


@router.get("/inventory.csv")
def inventory_csv(session: Session = Depends(get_session)) -> Response:
    service = ReportingService(session)
    csv_content = service.export_inventory_csv()
    return Response(content=csv_content, media_type="text/csv")


