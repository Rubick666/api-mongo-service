from fastapi import status

def test_list_products_empty(client):
    resp = client.get("/products")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []

def test_create_product_via_bulk_import(client, admin_token):
    csv = "name,price,category,brand,inventory_count\nImported,9.99,Gadgets,Acme,10"
    resp = client.post(
        "/products/bulk-import",
        files={"file": ("prod.csv", csv, "text/csv")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == status.HTTP_202_ACCEPTED
    assert resp.json()["imported"] == 1

    # Check it appears in list
    list_resp = client.get("/products")
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["name"] == "Imported"

def test_read_product_by_id(client, sample_product):
    prod_id = sample_product["id"]
    resp = client.get(f"/products/{prod_id}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["name"] == "Test Product"

def test_read_product_invalid_id(client):
    resp = client.get("/products/123")  # invalid ObjectId
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

def test_read_deleted_product_returns_404(client, admin_token, sample_product):
    prod_id = sample_product["id"]
    # Delete it
    del_resp = client.delete(
        f"/products/{prod_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    # Try to read it
    get_resp = client.get(f"/products/{prod_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND

def test_update_product_admin(client, admin_token, sample_product):
    prod_id = sample_product["id"]
    update_resp = client.patch(
        f"/products/{prod_id}",
        json={"price": 99.99, "inventory_count": 200},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_resp.status_code == status.HTTP_200_OK
    assert update_resp.json()["price"] == 99.99
    assert update_resp.json()["inventory_count"] == 200

def test_update_product_readonly_forbidden(client, readonly_token, sample_product):
    prod_id = sample_product["id"]
    update_resp = client.patch(
        f"/products/{prod_id}",
        json={"price": 1.00},
        headers={"Authorization": f"Bearer {readonly_token}"}
    )
    assert update_resp.status_code == status.HTTP_403_FORBIDDEN

def test_search_text(client, admin_token, sample_product):
    # Bulk import a specific product with unique text
    csv = "name,price,category,brand\nUniqueSearchItem,5.00,Electronics,Acme"
    client.post(
        "/products/bulk-import",
        files={"file": ("test.csv", csv, "text/csv")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    resp = client.post("/products/search", json={"text": "UniqueSearch"})
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "UniqueSearchItem"

def test_search_attribute_filter(client, admin_token):
    csv = "name,price,category,brand,material\nAttrTest,10.00,Hardware,ToolCo,carbon"
    client.post(
        "/products/bulk-import",
        files={"file": ("test.csv", csv, "text/csv")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    resp = client.post("/products/search", json={"attributes": {"material": "carbon"}})
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "AttrTest"