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