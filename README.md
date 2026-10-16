# OrderFlow API

OrderFlow API is a Python backend project for managing a product catalog and its stock values. It provides a REST API built with FastAPI, PostgreSQL persistence through SQLAlchemy, database migrations with Alembic, and automated schema and API tests.

The current implementation focuses on products. Order processing, authentication, and stock movement tracking are not implemented.

## Technologies

- **FastAPI**: routing, dependency injection, and generated OpenAPI documentation.
- **Pydantic**: request validation and response schemas.
- **SQLAlchemy**: typed ORM models and database sessions.
- **PostgreSQL and Psycopg 3**: relational storage and database connectivity.
- **Alembic**: versioned database migrations.
- **Uvicorn**: ASGI application server.
- **pytest, FastAPI TestClient, and HTTPX**: automated testing.
- **python-dotenv**: local environment configuration.

Dependencies are pinned in `requirements.txt`.

## Available functionality

- Create, list, retrieve, update, and delete products.
- List products in ascending ID order.
- Validate product names, decimal prices, and nonnegative stock values.
- Enforce positive prices and nonnegative stock at the database level.
- Return `404` responses for missing products.
- Expose application status endpoints and interactive API documentation.

Product prices use Python `Decimal` and PostgreSQL `NUMERIC(12, 2)`. JSON responses represent prices as strings.

**Current limitation:** `description` exists in the database model and API schemas, but the create and update routes do not persist this field. Sending it in a request does not save or update it.

## Project structure

```text
orderflow-api/
|-- app/
|   |-- main.py                 # FastAPI application and status endpoints
|   |-- database.py             # Engine, sessions, and database dependency
|   |-- models/products.py      # SQLAlchemy product model
|   |-- routes/products.py      # Product endpoints
|   `-- schemas/products.py     # Pydantic request and response schemas
|-- alembic/
|   |-- env.py                  # Migration configuration using app database settings
|   `-- versions/               # Product table and description migrations
|-- tests/
|   |-- conftest.py             # Test database setup and dependency override
|   |-- test_health.py          # Health endpoint test
|   |-- test_product_schema.py  # Schema validation tests
|   `-- test_products_api.py    # Product CRUD and missing-product tests
|-- alembic.ini
|-- requirements.txt
`-- README.md
```

## Requirements

- Python 3 and `pip`, compatible with the pinned dependencies. The repository does not declare a supported Python version range.
- A running PostgreSQL instance and a local development database.
- A **separate PostgreSQL database used exclusively for automated testing**.
- Database roles with the necessary permissions: migrations and test fixtures create and drop database objects.

## Local installation

Run the following commands from the repository root. Examples use Windows PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Environment configuration

The application reads `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME` through `app/database.py`. It loads a local `.env` file with python-dotenv. `DB_PORT` defaults to `5432` when omitted.

The following is the proposed **`.env.example` template**, included here because this documentation change only adds `README.md`. Save this template locally as `.env.example`, then copy it to `.env` and replace the placeholders with your local development settings.

```dotenv
DB_USER=orderflow_dev_user
DB_PASSWORD=replace_with_local_development_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=orderflow_dev
```

```powershell
Copy-Item .env.example .env
```

Create the PostgreSQL database and role before running migrations; the application does not provision them. Keep credentials out of version control. The existing `.gitignore` excludes `.env` and `.env.*`, with an exception for `.env.example`; only placeholders belong in that example file.

### Database migrations

After configuring `.env` for the local development database, apply the migrations:

```powershell
python -m alembic upgrade head
```

Alembic uses the database configuration from `app/database.py`. Application startup does not create tables automatically.

## Run the API

```powershell
python -m uvicorn app.main:app --reload
```

- API base URL: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

`--reload` is intended for local development.

## Endpoints

| Method | Path | Behavior | Success status |
| --- | --- | --- | --- |
| GET | `/` | Return `{"message": "OrderFlow API is running"}` | 200 |
| GET | `/health` | Return `{"status": "healthy"}` | 200 |
| POST | `/products/` | Create a product | 201 |
| GET | `/products/` | List all products, ordered by ID | 200 |
| GET | `/products/{product_id}` | Retrieve a product | 200 |
| PUT | `/products/{product_id}` | Update name, price, and stock | 200 |
| DELETE | `/products/{product_id}` | Delete a product; return no response body | 204 |

The health endpoint returns a static application status; it does not check database connectivity. Product listing does not currently provide pagination or filtering.

### Product request

`POST` and `PUT` use the same request schema. `PUT` requires all three fields below; it is not a partial update.

```json
{
  "name": "Mechanical Keyboard",
  "price": "250000.00",
  "stock": 10
}
```

| Field | Validation |
| --- | --- |
| `name` | Required string, 2–100 characters |
| `price` | Required decimal greater than zero, up to 12 digits and 2 decimal places |
| `stock` | Required integer greater than or equal to zero |
| `description` | Optional nullable string, up to 255 characters; currently not persisted by the write endpoints |

Example response for a newly created product:

```json
{
  "name": "Mechanical Keyboard",
  "description": null,
  "price": "250000.00",
  "stock": 10,
  "id": 1
}
```

The ID is generated by the database. Missing products return `404` with `{"detail": "Product not found"}`. Invalid request data returns FastAPI's `422` validation response.

## Automated tests

> **Destructive database setup:** Before each test that uses the `db` fixture, `tests/conftest.py` calls `Base.metadata.drop_all()` and `Base.metadata.create_all()` against the configured test database. Never run these tests against the main application database, a development database containing useful data, or any shared or production database. Use a disposable PostgreSQL database exclusively for testing.

### Configure an isolated test database

1. Create a separate PostgreSQL database, for example `orderflow_test`, and preferably a dedicated role whose permissions are limited to that database.
2. Create `.env.test` in the repository root using the template below. Replace every placeholder with settings for the dedicated test database.
3. Verify all five variables before invoking pytest. `DB_NAME` must identify the exclusive test database, not the database used by the API.

```dotenv
DB_USER=orderflow_test_user
DB_PASSWORD=replace_with_local_test_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=orderflow_test
```

`tests/conftest.py` loads `.env.test` with `override=True` before importing the application, then overrides the API's database dependency with a test session. It does **not** enforce a test database name or prevent destructive operations against an incorrectly configured database. A missing or incomplete `.env.test` can leave values inherited from the shell or loaded from `.env`; provide every variable explicitly.

The fixture creates the product tables directly from SQLAlchemy metadata, so these integration tests do not require Alembic migrations and do not validate the migration history.

### Run the suite

Only after verifying the isolated test configuration, run from the repository root:

```powershell
python -m pytest -v
```

The existing suite contains 12 tests covering:

- The health endpoint response.
- Valid product schemas and rejection of negative prices and stock.
- Product creation, listing, retrieval, update, and deletion.
- `404` responses when retrieving, updating, or deleting a missing product.

Test results depend on the local environment and an accessible test database. This README does not claim a passing run or a coverage percentage.
