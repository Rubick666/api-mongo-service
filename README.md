# Product Catalog API (api-mongo-service)

A flexible product catalog service using MongoDB, FastAPI, and Beanie.

## Quick Start

1. Clone the repo.
2. Run `docker-compose up` from the project root.
3. Visit `http://localhost:8000/health` to verify service is up.
4. OpenAPI docs at `http://localhost:8000/docs`.

## Environment

Copy `.env.example` to `.env` and adjust as needed. Defaults work with Docker Compose.

## Development

- Run tests: `pytest` (coming soon).
- Code is organized as FastAPI modular structure: `app/routers`, `app/models`, `app/services`.

## Seed the Database

To populate the database with sample product data:

```bash
docker-compose exec api python -m scripts.seed_db

## Index Design & Performance

MongoDB’s performance depends on proper indexing. This service defines four strategic indexes to support its most common query patterns.

| Index Name | Fields | Query Pattern It Supports |
|------------|--------|---------------------------|
| `text_search` | `name` (TEXT), `description` (TEXT) | Full‑text search via `$text` in `POST /products/search` – enables fast, relevance‑ranked lookup over product names and descriptions. |
| `category_brand` | `category` (ASC), `brand` (ASC) | Filtered listing via `GET /products?category=X&brand=Y` – the compound index covers both filters with a single index scan. |
| `price_asc` | `price` (ASC) | Price‑range queries (`min_price`/`max_price`) in `POST /products/search` – allows MongoDB to quickly find products within the range. |
| `active_created_desc` | `is_active` (ASC), `created_at` (DESC) | Default paginated listing (`GET /products`) – returns only active products, newest first, without scanning the entire collection. |

**Why this matters:**  
Without these indexes, MongoDB would perform a collection scan for every request – slow and unscalable. With them, queries run in milliseconds even with thousands of products. These indexes are created automatically on application startup via Beanie’s `Settings.indexes` definition.

**Future optimisation:**  
If attribute filtering becomes a bottleneck, we can add a wildcard index on `attributes` or specific keys (`attributes.material`, `attributes.voltage`) – but for now, the flexible schema works well without over‑indexing.