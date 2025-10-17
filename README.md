# Inventory Management System

This project provides a command-line driven Inventory Management System (IMS) built with Python, SQLite, and SQLAlchemy. It supports:

- Item and category management, including barcode generation and inventory adjustments.
- Supplier tracking with purchase orders, inbound shipments, and performance analytics.
- Customer relationship management with loyalty programs and outstanding balance tracking.
- Order processing, payment tracking, and automated stock movements.
- Reporting dashboards for sales, inventory status, and supplier metrics.
- Role-based user registry with activity logs.

## Getting Started

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Initialise the database:

   ```bash
   python -m ims.cli initdb
   ```

## Usage

The CLI exposes high-level commands. Examples:

```bash
python -m ims.cli add_category "Electronics"
python -m ims.cli add_item SKU-001 "Laptop" --unit-price 899.99 --stock-quantity 10 --reorder-level 2
python -m ims.cli create_supplier "Tech Supplies" "Alex Doe"
python -m ims.cli create_customer "Jane Smith" --email jane@example.com
python -m ims.cli create_purchase_order 1 1:5:799.99 --expected-days 7
python -m ims.cli receive_shipment 1 "Alex" 1:5
python -m ims.cli create_order 1 1:1
python -m ims.cli reports summary
```

To export inventory to CSV:

```bash
python -m ims.cli export_inventory_csv inventory.csv
```

## Development

The project stores state in `ims/ims.sqlite3`. Delete the file to reset data during local development.

