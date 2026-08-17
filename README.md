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

* Run tests with `pytest` (coming soon).
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

* ✅ JWT authentication with role-based access (`admin` vs `readonly`)
* ✅ MongoDB schema validation (JSON Schema) at the collection level
* ✅ Text index and compound indexes, with this README explaining why each exists
* ✅ Aggregation pipeline endpoints:

  * `/products/analytics/categories`
  * `/products/analytics/price-distribution`
* ✅ Rate-limiting middleware:

  * Authentication: 5 requests/minute
  * Search: 100 requests/minute
  * Import: 10 requests/minute
* ✅ `pytest` test suite with a dedicated test database
* ✅ Bulk import endpoint supporting CSV/JSONL streaming
* ✅ Soft-delete and versioning with automatic `updated_at` updates

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
