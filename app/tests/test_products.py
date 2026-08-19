from fastapi import status


def test_list_products_empty(client):
    response = client.get("/products")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_create_product_via_bulk_import(client, admin_token):
    csv = (
        "name,price,category,brand,inventory_count\n"
        "Imported,9.99,Gadgets,Acme,10"
    )

    response = client.post(
        "/products/bulk-import",
        files={
            "file": (
                "prod.csv",
                csv,
                "text/csv",
            )
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["imported"] == 1

    list_response = client.get("/products")

    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == "Imported"


def test_read_product_by_id(client, sample_product):
    product_id = sample_product["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Test Product"


def test_read_product_invalid_id(client):
    response = client.get("/products/123")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_read_deleted_product_returns_404(
    client,
    admin_token,
    sample_product,
):
    product_id = sample_product["id"]

    delete_response = client.delete(
        f"/products/{product_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get(f"/products/{product_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_product_admin(
    client,
    admin_token,
    sample_product,
):
    product_id = sample_product["id"]

    response = client.patch(
        f"/products/{product_id}",
        json={
            "price": 99.99,
            "inventory_count": 200,
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["price"] == 99.99
    assert response.json()["inventory_count"] == 200


def test_update_product_readonly_forbidden(
    client,
    readonly_token,
    sample_product,
):
    product_id = sample_product["id"]

    response = client.patch(
        f"/products/{product_id}",
        json={
            "price": 1.00,
        },
        headers={
            "Authorization": f"Bearer {readonly_token}"
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_search_text(
    client,
    admin_token,
    sample_product,
):
    csv = (
        "name,price,category,brand\n"
        "UniqueSearchItem,5.00,Electronics,Acme"
    )

    import_response = client.post(
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

    assert import_response.status_code == status.HTTP_202_ACCEPTED

    response = client.post(
        "/products/search",
        json={
            "text": "UniqueSearch"
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "UniqueSearchItem"


def test_search_attribute_filter(client, admin_token):
    csv = (
        "name,price,category,brand,material\n"
        "AttrTest,10.00,Hardware,ToolCo,carbon"
    )

    import_response = client.post(
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

    assert import_response.status_code == status.HTTP_202_ACCEPTED

    response = client.post(
        "/products/search",
        json={
            "attributes": {
                "material": "carbon"
            }
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "AttrTest"