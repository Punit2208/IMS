"""Command-line interface for the Inventory Management System."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path
from typing import Optional

import typer

from .database import Base, engine
from .services.customer_service import CustomerService
from .services.inventory_service import InventoryService
from .services.order_service import OrderService
from .services.reporting_service import ReportingService
from .services.supplier_service import SupplierService
from .services.supply_service import SupplyService
from .services.user_service import UserService

app = typer.Typer(help="Inventory Management System CLI")


@app.command()
def initdb(force: bool = typer.Option(False, help="Drop and recreate all tables")) -> None:
    """Initialise the SQLite database."""
    if force:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    typer.secho("Database initialised", fg=typer.colors.GREEN)


@app.command()
def add_category(name: str, description: Optional[str] = None) -> None:
    with InventoryService() as service:
        service.create_category(name=name, description=description)
    typer.echo(f"Created category {name}")


@app.command()
def list_categories() -> None:
    with InventoryService() as service:
        for category in service.list_categories():
            typer.echo(f"{category.id}: {category.name} - {category.description or ''}")


@app.command()
def add_item(
    sku: str,
    name: str,
    unit_price: float,
    category_id: Optional[int] = typer.Option(None),
    description: Optional[str] = typer.Option(None),
    unit: str = typer.Option("unit"),
    stock_quantity: int = typer.Option(0),
    reorder_level: int = typer.Option(0),
) -> None:
    with InventoryService() as service:
        service.create_item(
            sku=sku,
            name=name,
            unit_price=Decimal(str(unit_price)),
            category_id=category_id,
            description=description,
            unit=unit,
            stock_quantity=stock_quantity,
            reorder_level=reorder_level,
        )
    typer.echo(f"Created item {sku}")


@app.command()
def list_items(category_id: Optional[int] = typer.Option(None)) -> None:
    with InventoryService() as service:
        for item in service.list_items(category_id=category_id):
            typer.echo(
                f"{item.id}: {item.sku} - {item.name} qty={item.stock_quantity} reorder={item.reorder_level} price={item.unit_price}"
            )


@app.command()
def low_stock() -> None:
    with InventoryService() as service:
        alerts = service.low_stock_alerts()
    if not alerts:
        typer.echo("No low stock items")
        return
    typer.echo("Low stock alerts:")
    for alert in alerts:
        typer.echo(f"{alert.sku} ({alert.name}) qty={alert.quantity} reorder={alert.reorder_level}")


@app.command()
def create_supplier(company_name: str, contact_name: Optional[str] = None) -> None:
    with SupplierService() as service:
        service.create_supplier(company_name=company_name, contact_name=contact_name)
    typer.echo(f"Created supplier {company_name}")


@app.command()
def list_suppliers() -> None:
    with SupplierService() as service:
        for supplier in service.list_suppliers():
            typer.echo(f"{supplier.id}: {supplier.company_name} contact={supplier.contact_name or ''}")


@app.command()
def link_supplier_item(supplier_id: int, item_id: int) -> None:
    with SupplierService() as service:
        service.link_item(supplier_id=supplier_id, item_id=item_id)
    typer.echo(f"Linked supplier {supplier_id} to item {item_id}")


@app.command()
def create_customer(name: str, email: Optional[str] = None) -> None:
    with CustomerService() as service:
        service.create_customer(name=name, email=email)
    typer.echo(f"Created customer {name}")


@app.command()
def list_customers() -> None:
    with CustomerService() as service:
        for customer in service.list_customers():
            typer.echo(f"{customer.id}: {customer.name} loyalty={customer.loyalty_points}")


@app.command()
def create_purchase_order(
    supplier_id: int,
    item_lines: list[str] = typer.Argument(..., help="ITEM_ID:QTY:UNIT_COST"),
    expected_days: Optional[int] = typer.Option(None, help="Days until expected delivery"),
) -> None:
    items = []
    for line in item_lines:
        item_id, qty, cost = line.split(":")
        items.append((int(item_id), int(qty), Decimal(cost)))
    expected_date = dt.date.today() + dt.timedelta(days=expected_days) if expected_days else None
    with SupplyService() as service:
        po = service.create_purchase_order(supplier_id=supplier_id, items=items, expected_date=expected_date)
    typer.echo(f"Created PO {po.id} total={po.total_cost}")


@app.command()
def receive_shipment(
    purchase_order_id: int,
    received_by: str,
    received_lines: list[str] = typer.Argument(..., help="ITEM_ID:QTY"),
) -> None:
    lines = []
    for line in received_lines:
        item_id, qty = line.split(":")
        lines.append((int(item_id), int(qty)))
    with SupplyService() as service:
        shipment = service.receive_shipment(
            purchase_order_id=purchase_order_id,
            received_by=received_by,
            received_lines=lines,
        )
    typer.echo(f"Received shipment {shipment.id} on_time={shipment.on_time}")


@app.command()
def auto_reorder(minimum_quantity: int = typer.Option(1)) -> None:
    with SupplyService() as service:
        orders = service.auto_reorder(minimum_quantity=minimum_quantity)
    if not orders:
        typer.echo("No items eligible for auto reorder")
        return
    for order in orders:
        typer.echo(f"Created auto PO {order.id} supplier={order.supplier.company_name} total={order.total_cost}")


@app.command()
def create_order(
    customer_id: int,
    items: list[str] = typer.Argument(..., help="ITEM_ID:QTY"),
) -> None:
    parsed_items = []
    for entry in items:
        item_id, qty = entry.split(":")
        parsed_items.append((int(item_id), int(qty)))
    with OrderService() as service:
        order = service.create_order(customer_id=customer_id, items=parsed_items)
    typer.echo(f"Created order {order.id} total={order.total}")


@app.command()
def list_orders(customer_id: Optional[int] = typer.Option(None)) -> None:
    with OrderService() as service:
        for order in service.list_orders(customer_id=customer_id):
            typer.echo(f"{order.id}: {order.status} total={order.total} created={order.created_at}")


@app.command()
def record_payment(order_id: int, amount: float, method: str = typer.Option("cash")) -> None:
    with OrderService() as service:
        service.record_payment(order_id=order_id, amount=Decimal(str(amount)), method=method)
    typer.echo("Payment recorded")


@app.command()
def reports(report_type: str = typer.Argument(..., help="summary|inventory|sales_trends")) -> None:
    with ReportingService() as service:
        if report_type == "summary":
            summary = service.sales_summary()
            typer.echo(f"Orders: {summary.total_orders} Revenue: {summary.total_revenue} AOV: {summary.average_order_value}")
        elif report_type == "inventory":
            for status in service.inventory_status():
                typer.echo(
                    f"{status.sku}: {status.name} qty={status.stock_quantity} reorder={status.reorder_level}"
                )
        elif report_type == "sales_trends":
            for period, total in service.sales_trends().items():
                typer.echo(f"{period}: {total}")
        else:
            raise typer.BadParameter("Unknown report type")


@app.command()
def export_inventory_csv(output: Path) -> None:
    with ReportingService() as service:
        csv_data = service.export_inventory_csv()
    output.write_text(csv_data)
    typer.echo(f"Exported inventory to {output}")


@app.command()
def export_supplier_performance(output: Optional[Path] = typer.Option(None)) -> None:
    with ReportingService() as service:
        data = service.supplier_performance()
    lines = ["supplier_id,on_time_rate,orders"]
    for supplier_id, metrics in data.items():
        lines.append(f"{supplier_id},{metrics['on_time_rate']:.2f},{metrics['orders']}")
    text = "\n".join(lines)
    if output:
        output.write_text(text)
        typer.echo(f"Exported supplier performance to {output}")
    else:
        typer.echo(text)


@app.command()
def generate_barcode(sku: str, output: Path) -> None:
    with InventoryService() as service:
        image_bytes = service.generate_barcode_image(sku)
    output.write_bytes(image_bytes)
    typer.echo(f"Saved barcode for {sku} to {output}")


@app.command()
def create_user(username: str, role: str, full_name: Optional[str] = None) -> None:
    with UserService() as service:
        service.create_user(username=username, full_name=full_name, role=role)
    typer.echo(f"Created user {username}")


@app.command()
def activity_feed(limit: int = typer.Option(20)) -> None:
    with UserService() as service:
        for log in service.activity_feed(limit=limit):
            typer.echo(f"{log.created_at} - {log.action}: {log.details or ''}")


if __name__ == "__main__":
    app()
