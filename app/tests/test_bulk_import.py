from fastapi import status


def test_bulk_import_csv_success(client, admin_token):
    csv = (
        "name,price,category,brand,inventory_count,description\n"
        "Test,12.50,Electronics,Acme,100,desc"
    )

    response = client.post(
        "/products/bulk-import",
        files={
            "file": (
                "data.csv",
                csv,
                "text/csv",
            )
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()

    assert data["imported"] == 1
    assert data["errors"] == []


def test_bulk_import_jsonl_success(client, admin_token):
    jsonl = (
        '{"name":"J1","price":5.0,"category":"Books","brand":"Pub"}\n'
        '{"name":"J2","price":6.0,"category":"Books","brand":"Pub"}'
    )

    response = client.post(
        "/products/bulk-import",
        files={
            "file": (
                "data.jsonl",
                jsonl,
                "application/json",
            )
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()

    assert data["imported"] == 2
    assert data["errors"] == []


def test_bulk_import_partial_errors(client, admin_token):
    csv = (
        "name,price,category,brand\n"
        "Valid,10,A,X\n"
        "Invalid,,B,Y"
    )

    response = client.post(
        "/products/bulk-import",
        files={
            "file": (
                "data.csv",
                csv,
                "text/csv",
            )
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()

    assert data["imported"] == 1
    assert len(data["errors"]) == 1
    assert "price" in data["errors"][0]["error"].lower()


def test_bulk_import_requires_admin(client, readonly_token):
    csv = "name,price,category,brand\nTest,1,A,X"

    response = client.post(
        "/products/bulk-import",
        files={
            "file": (
                "data.csv",
                csv,
                "text/csv",
            )
        },
        headers={
            "Authorization": f"Bearer {readonly_token}"
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN