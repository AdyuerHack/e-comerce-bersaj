import os
import tempfile
import pytest

# Use a temporary DB for tests
temp_db_fd, temp_db_path = tempfile.mkstemp()
os.environ["CATALOG_DB_PATH"] = temp_db_path

from app import app
from database import init_db, get_connection


@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    yield
    # Cleanup will happen on exit or reset if needed


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "catalog_inventory_service"


def test_list_products(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    products = response.get_json()
    assert len(products) >= 3
    assert "tallas" in products[0]


def test_get_product_detail(client):
    response = client.get("/api/v1/products/1")
    assert response.status_code == 200
    product = response.get_json()
    assert product["id"] == 1
    assert product["nombre"] == "Camiseta Básica Oversize"
    assert len(product["tallas"]) > 0


def test_get_product_not_found(client):
    response = client.get("/api/v1/products/9999")
    assert response.status_code == 404


def test_get_talla_detail(client):
    response = client.get("/api/v1/tallas/1")
    assert response.status_code == 200
    talla = response.get_json()
    assert talla["id"] == 1
    assert talla["precio"] == 45000.00


def test_check_stock_available(client):
    payload = {"items": [{"talla_id": 1, "cantidad": 2}]}
    response = client.post("/api/v1/inventory/check", json=payload)
    assert response.status_code == 200
    assert response.get_json()["available"] is True


def test_check_stock_insufficient(client):
    payload = {"items": [{"talla_id": 1, "cantidad": 9999}]}
    response = client.post("/api/v1/inventory/check", json=payload)
    assert response.status_code == 409
    assert response.get_json()["available"] is False


def test_decrease_stock_success_and_conflict(client):
    # First, get current stock
    talla_before = client.get("/api/v1/tallas/2").get_json()
    initial_stock = talla_before["stock"]

    # Deduct 3 units
    payload = {"items": [{"talla_id": 2, "cantidad": 3}]}
    response = client.post("/api/v1/inventory/decrease", json=payload)
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    # Check new stock
    talla_after = client.get("/api/v1/tallas/2").get_json()
    assert talla_after["stock"] == initial_stock - 3

    # Try to deduct more than remaining
    excessive_payload = {"items": [{"talla_id": 2, "cantidad": initial_stock + 10}]}
    fail_response = client.post("/api/v1/inventory/decrease", json=excessive_payload)
    assert fail_response.status_code == 409


def test_public_catalog_endpoint(client):
    response = client.get("/api/v1/public/catalog")
    assert response.status_code == 200
    data = response.get_json()
    assert "tienda" in data
    assert "productos" in data
    assert len(data["productos"]) >= 3

