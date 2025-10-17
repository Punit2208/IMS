"""Pydantic schemas used by the web API."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryRead(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Item schemas
class ItemBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    unit: str = "unit"
    unit_price: Decimal
    stock_quantity: int = 0
    reorder_level: int = 0
    image_path: Optional[str] = None
    category_id: Optional[int] = Field(default=None, description="Associated category identifier")


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    reorder_level: Optional[int] = None
    image_path: Optional[str] = None
    category_id: Optional[int] = None


class ItemRead(ItemBase):
    id: int
    barcode: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StockAdjustment(BaseModel):
    quantity_change: int
    reason: str
    reference: Optional[str] = None


class InventoryTransactionRead(BaseModel):
    id: int
    item_id: int
    change: int
    reason: str
    reference: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LowStockAlertRead(BaseModel):
    sku: str
    name: str
    quantity: int
    reorder_level: int
    model_config = ConfigDict(from_attributes=True)


class InventoryValuationRead(BaseModel):
    total_value: Decimal


class BarcodeRead(BaseModel):
    value: str
    image_base64: str


# Supplier schemas
class SupplierBase(BaseModel):
    company_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None


class SupplierRead(SupplierBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SupplierLinkItem(BaseModel):
    item_id: int


class SupplierBalanceRead(BaseModel):
    supplier_id: int
    outstanding_balance: Decimal


class SupplierPerformanceRead(BaseModel):
    supplier_id: int
    company_name: str
    on_time_rate: float
    average_delivery_days: Optional[float]
    total_orders: int
    accuracy_rate: Optional[float]
    model_config = ConfigDict(from_attributes=True)


# Purchase order and shipment schemas
class PurchaseOrderLineCreate(BaseModel):
    item_id: int
    quantity: int
    unit_cost: Decimal


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    items: list[PurchaseOrderLineCreate]
    expected_date: Optional[date] = None


class PurchaseOrderLineRead(BaseModel):
    id: int
    item_id: int
    quantity: int
    unit_cost: Decimal
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderRead(BaseModel):
    id: int
    supplier_id: int
    expected_date: Optional[date]
    status: str
    total_cost: Decimal
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineRead]
    model_config = ConfigDict(from_attributes=True)


class ShipmentLine(BaseModel):
    item_id: int
    quantity: int


class ShipmentCreate(BaseModel):
    purchase_order_id: int
    received_by: str
    received_lines: list[ShipmentLine]
    received_date: Optional[datetime] = None
    notes: Optional[str] = None


class ShipmentRead(BaseModel):
    id: int
    purchase_order_id: int
    received_date: Optional[datetime]
    received_by: Optional[str]
    notes: Optional[str]
    on_time: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Customer schemas
class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    preferences: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    preferences: Optional[str] = None


class CustomerRead(CustomerBase):
    id: int
    loyalty_points: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LoyaltyAdjustment(BaseModel):
    points: int


class OutstandingBalanceRead(BaseModel):
    customer_id: int
    outstanding_balance: Decimal


# Order schemas
class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int


class OrderCreate(BaseModel):
    customer_id: int
    items: list[OrderItemCreate]
    notes: Optional[str] = None
    status: str = "pending"


class OrderItemRead(BaseModel):
    id: int
    item_id: int
    quantity: int
    unit_price: Decimal
    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    amount: Decimal
    method: str


class PaymentRead(BaseModel):
    id: int
    amount: Decimal
    method: str
    received_date: datetime
    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    customer_id: int
    status: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    order_items: list[OrderItemRead]
    payments: list[PaymentRead]
    model_config = ConfigDict(from_attributes=True)


class OutstandingOrderBalanceRead(BaseModel):
    order_id: int
    outstanding_balance: Decimal


class OrderStatusUpdate(BaseModel):
    status: str


# Reporting schemas
class SalesSummaryRead(BaseModel):
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal


class InventoryStatusRead(BaseModel):
    sku: str
    name: str
    stock_quantity: int
    reorder_level: int
    model_config = ConfigDict(from_attributes=True)


class SalesTrendRead(BaseModel):
    period: str
    total: Decimal


class AutoReorderRequest(BaseModel):
    minimum_quantity: int = 1


class AutoReorderResponse(BaseModel):
    created_orders: list[int]


