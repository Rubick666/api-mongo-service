# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient
from app.core.config import settings
from app.main import app, init_db
from app.models.product import Product
from app.models.user import User

# Force testing mode and test DB name
os.environ["TESTING"] = "1"
settings.testing = True
settings.mongo_db_name = "catalog_test_db"

@pytest.fixture(scope="session")
async def test_db():
    """Initialize the test database once per session."""
    client = AsyncMongoClient(settings.mongo_uri)
    # Drop and recreate
    await client.drop_database(settings.mongo_db_name)
    await init_db()
    print(f"Connected to test database: {settings.mongo_db_name}")
    yield
    # Cleanup after all tests
    await Product.delete_all()
    await User.delete_all()
    await client.drop_database(settings.mongo_db_name)
    await client.close()

@pytest.fixture(autouse=True)
async def clean_db_before_test():
    """Clear collections before each test."""
    await Product.delete_all()
    await User.delete_all()

@pytest.fixture
def client(test_db):
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def admin_token(client):
    resp = client.post("/auth/register",
                       json={"email": "admin@test.com", "password": "adminpass123"})
    assert resp.status_code == 201
    return resp.json()["access_token"]

@pytest.fixture
async def readonly_token(client):
    resp = client.post("/auth/register",
                       json={"email": "user@test.com", "password": "userpass123"})
    assert resp.status_code == 201
    return resp.json()["access_token"]

@pytest.fixture
async def sample_product(client, admin_token):
    token = await admin_token
    csv = "name,price,category,brand,inventory_count,description\nTest Product,19.99,Electronics,TestBrand,50,Test desc"
    resp = client.post("/products/bulk-import",
                       files={"file": ("test.csv", csv, "text/csv")},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 202
    list_resp = client.get("/products")
    assert list_resp.status_code == 200
    return list_resp.json()[0]