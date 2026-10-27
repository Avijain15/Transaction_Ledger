# Transaction Ledger API

A FastAPI service for creating accounts, recording immutable credit and debit entries, reading balances and history, and transferring money atomically between accounts. PostgreSQL enforces ledger constraints and protects transactions from direct updates and deletes.

## Prerequisites

- Python 3.11
- Docker Desktop with Docker Compose

## Run locally (PowerShell)

1. Start PostgreSQL 16:

   ```powershell
   docker compose up -d db
   ```

2. Create and activate a virtual environment, then install the pinned dependencies:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Start the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

   Tables and the transaction immutability trigger are created idempotently at application startup. The default database URL is `postgresql+psycopg://ledger:ledger@localhost:5432/ledger`; set `DATABASE_URL` to use another database.

4. Open the frontend at [http://localhost:8000/](http://localhost:8000/) or FastAPI's interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Project structure

The `app/` directory contains the FastAPI app, routers, services, SQLAlchemy models, schemas, errors, and static frontend. `docs/API.md` documents endpoints and curl examples; `docs/ASSUMPTIONS.md` records implementation assumptions.
