# Inventory Management System

This project delivers a FastAPI-powered web application for managing inventory, suppliers, customers, and sales. It exposes a REST API alongside a lightweight HTML dashboard so teams can monitor stock levels, orchestrate purchase orders, and analyse sales performance.

## Features

- **Inventory & Categories** – Track SKUs, pricing, reorder levels, barcode imagery, and categorisation with low stock alerts and valuation reporting.
- **Suppliers & Purchasing** – Maintain supplier relationships, create purchase orders, receive shipments, and analyse on-time performance.
- **Customers & Orders** – Capture customer profiles, loyalty balances, sales orders, payments, and outstanding balances.
- **Reporting & Analytics** – Export inventory snapshots, review sales trends, and view KPIs on the built-in dashboard.
- **Automation** – Auto-generate purchase orders for items falling below their reorder thresholds.

## Getting Started

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the web application with Uvicorn:

   ```bash
   uvicorn ims.app:app --reload
   ```

   The dashboard will be available at [http://localhost:8000/](http://localhost:8000/) and the interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

4. (Optional) Remove the SQLite database file `ims/ims.sqlite3` to reset the environment.

## API Overview

The REST API is organised into functional groups:

| Area | Base Path | Highlights |
| --- | --- | --- |
| Inventory | `/inventory` | Manage categories, items, stock adjustments, barcode exports, and valuation metrics. |
| Suppliers | `/suppliers` | CRUD, item linking, purchase history, outstanding balances, and performance metrics. |
| Supply Chain | `/supply` | Create purchase orders, receive shipments, view expected receipts, and trigger auto-reorders. |
| Customers | `/customers` | Manage profiles, balances, and loyalty programs. |
| Orders | `/orders` | Create orders, update status, record payments, and review outstanding balances. |
| Reports | `/reports` | Retrieve sales summaries, inventory status, trends, and CSV exports. |

Refer to the interactive Swagger UI for detailed request/response schemas.

## Development Notes

- SQLAlchemy powers persistence with a bundled SQLite database located at `ims/ims.sqlite3`.
- Pydantic models in `ims/schemas.py` define the API contract between services and routes.
- Services encapsulate domain logic and are reused across both the API and HTML dashboard.
- The dashboard templates live under `ims/templates/` and render summary analytics using the same services.

Contributions and enhancements are welcome—fork the repository, make your changes, and open a pull request.
