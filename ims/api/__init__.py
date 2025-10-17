"""API router aggregation for the Inventory Management System."""
from __future__ import annotations

from fastapi import APIRouter

from .routes_inventory import router as inventory_router
from .routes_suppliers import router as supplier_router
from .routes_customers import router as customer_router
from .routes_orders import router as order_router
from .routes_supply import router as supply_router
from .routes_reporting import router as reporting_router

api_router = APIRouter()
api_router.include_router(inventory_router)
api_router.include_router(supplier_router)
api_router.include_router(customer_router)
api_router.include_router(order_router)
api_router.include_router(supply_router)
api_router.include_router(reporting_router)

__all__ = ["api_router"]

