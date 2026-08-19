import os

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

# IMPORTANT: set testing mode BEFORE importing the application
os.environ["TESTING"] = "1"

from app.core.config import settings
from app.main import app


settings.testing = True
settings.mongo_db_name = "catalog_test_db"


@pytest.fixture
def client():
    # FastAPI/TestClient owns the event loop used by Beanie.
    # Let application startup initialize the database.
    with TestClient(app) as test_client:
        yield test_client

    # Clean the test database after each test using synchronous PyMongo.
    # This avoids AsyncMongoClient / event-loop conflicts.
    mongo = MongoClient(settings.mongo_uri)
    try:
        mongo.drop_database(settings.mongo_db_name)
    finally:
        mongo.close()


@pytest.fixture
def admin_token(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "admin@test.com",
            "password": "adminpass123",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["access_token"]


@pytest.fixture
def readonly_token(client):
    # First user -> admin
    first = client.post(
        "/auth/register",
        json={
            "email": "admin@test.com",
            "password": "adminpass123",
        },
    )

    assert first.status_code == 201, first.text

    # Second user -> readonly
    second = client.post(
        "/auth/register",
        json={
            "email": "user@test.com",
            "password": "userpass123",
        },
    )

    assert second.status_code == 201, second.text

    return second.json()["access_token"]


@pytest.fixture
def sample_product(client, admin_token):
    csv = (
        "name,price,category,brand,inventory_count,description\n"
        "Test Product,19.99,Electronics,TestBrand,50,Test desc"
    )

    response = client.post(
        "/products/bulk-import",
        files={
            "file": (
                "test.csv",
                csv,
                "text/csv",
            )
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 202, response.text
    assert response.json()["imported"] == 1

    products = client.get("/products")

    assert products.status_code == 200
    assert len(products.json()) == 1

    return products.json()[0]