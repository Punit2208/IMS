"""FastAPI application for the Inventory Management System."""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .api import api_router
from .api.dependencies import get_session
from .database import Base, engine
from .services.inventory_service import InventoryService
from .services.reporting_service import ReportingService
from .services.supply_service import SupplyService

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def create_app() -> FastAPI:
    app = FastAPI(title="Inventory Management System", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
        reporting = ReportingService(session)
        inventory = InventoryService(session)
        supply = SupplyService(session)
        summary = reporting.sales_summary()
        low_stock = inventory.low_stock_alerts()
        expected = supply.expected_receipts()
        valuation = inventory.inventory_valuation()
        context = {
            "request": request,
            "summary": summary,
            "low_stock": low_stock,
            "expected": expected,
            "valuation": valuation,
        }
        return templates.TemplateResponse("dashboard.html", context)

    return app


app = create_app()

__all__ = ["app", "create_app"]

