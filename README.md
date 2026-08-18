# Product Catalog API (`api-mongo-service`)

A flexible product catalog service using MongoDB, FastAPI, and Beanie.

## Quick Start

1. Clone the repository.
2. Run `docker-compose up` from the project root.
3. Visit `http://localhost:8000/health` to verify that the service is running.
4. Open the API documentation at `http://localhost:8000/docs`.

## Environment

Copy `.env.example` to `.env` and adjust the values as needed.

The default configuration works with Docker Compose.

## Development

* Run tests with `pytest`.
* The code is organized using a modular FastAPI structure:

  * `app/routers/`
  * `app/models/`
  * `app/services/`

## Seed the Database

To populate the database with sample product data:

```bash
docker-compose exec api python -m scripts.seed_db
```

## Index Design & Performance

MongoDB's performance depends heavily on proper indexing. This service defines four strategic indexes to support its most common query patterns.

| Index Name            | Fields                                 | Query Pattern It Supports                                                                                                                               |
| --------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `text_search`         | `name` (TEXT), `description` (TEXT)    | Full-text search via `$text` in `POST /products/search`, enabling fast, relevance-ranked lookups over product names and descriptions.                   |
| `category_brand`      | `category` (ASC), `brand` (ASC)        | Filtered listing via `GET /products?category=X&brand=Y`, allowing both filters to be handled by a single compound index.                                |
| `price_asc`           | `price` (ASC)                          | Price-range queries using `min_price` / `max_price` in `POST /products/search`, allowing MongoDB to quickly locate products within the requested range. |
| `active_created_desc` | `is_active` (ASC), `created_at` (DESC) | Default paginated listing via `GET /products`, returning active products in newest-first order without scanning the entire collection.                  |

### Why This Matters

Without these indexes, MongoDB may need to perform a collection scan for every request, which becomes slow and unscalable as the dataset grows.

With the appropriate indexes in place, these common queries can be executed efficiently even when the collection contains thousands of products.

The indexes are created automatically when the application starts through Beanie's `Settings.indexes` configuration.

### Future Optimization

If filtering by product attributes becomes a performance bottleneck, a wildcard index on `attributes` or indexes on frequently queried fields such as `attributes.material` or `attributes.voltage` can be added.

For now, the flexible schema works well without over-indexing the collection.

## Authentication & Authorization

The API uses **JWT (Bearer token)** authentication.

There are two available roles:

* `admin` — Full access, including bulk data import and product modification/deletion.
* `readonly` — Can only list and search products. This is the default role.

### Get a Token

#### Register

The first registered user becomes an administrator.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "password123"}'
```

#### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "password123"}'
```

## Feature Checklist

* ✅ **JWT auth with role-based access** – `admin` vs `readonly` (first user is admin).
* ✅ **MongoDB schema validation** – JSON Schema enforced at the collection level.
* ✅ **Text + compound indexes** – `text_search`, `category_brand`, `price_asc`, `active_created_desc` – with documentation.
* ✅ **Aggregation pipeline endpoints** – `/analytics/categories` and `/analytics/price-distribution`.
* ✅ **Rate limiting** – `5/min` on auth, `100/min` on search, `10/min` on bulk import.
* ✅ **Comprehensive pytest suite** – runs against a dedicated test database (`catalog_test_db`).
* ✅ **Bulk import** – streams CSV/JSONL with detailed error reporting and `BulkWriter`.
* ✅ **Soft-delete & versioning** – `is_active=False` and auto-updated `updated_at`.

## Testing

The service includes a complete integration test suite using `pytest`.

**Requirements:** MongoDB must be running. The `docker-compose.yml` starts MongoDB automatically.

### Run Tests

```bash
docker-compose exec api pytest tests/ -v
```

## API Endpoints

The following table provides the complete list of available API endpoints.

| Method   | Endpoint                                 | Description                                           | Auth  |
| -------- | ---------------------------------------- | ----------------------------------------------------- | ----- |
| `GET`    | `/health`                                | Service health check                                  | None  |
| `GET`    | `/products`                              | List active products (paginated)                      | None  |
| `POST`   | `/products/search`                       | Rich search with text, filters, price, and attributes | None  |
| `GET`    | `/products/{id}`                         | Fetch a single product                                | None  |
| `PATCH`  | `/products/{id}`                         | Update a product                                      | Admin |
| `DELETE` | `/products/{id}`                         | Soft-delete a product                                 | Admin |
| `POST`   | `/products/bulk-import`                  | Bulk import CSV/JSONL                                 | Admin |
| `GET`    | `/products/analytics/categories`         | Count products per category                           | None  |
| `GET`    | `/products/analytics/price-distribution` | Price histogram with dynamic buckets                  | None  |
| `POST`   | `/auth/register`                         | Register a new user                                   | None  |
| `POST`   | `/auth/login`                            | Login and obtain a JWT                                | None  |
| `GET`    | `/auth/me`                               | Get current user information                          | User  |
