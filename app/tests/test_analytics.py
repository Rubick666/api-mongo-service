def test_category_analytics(client, admin_token):
    csv = (
        "name,price,category,brand\n"
        "Cat1,10,A,Acme\n"
        "Cat2,20,B,Acme\n"
        "Cat3,30,A,Acme"
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

    assert import_response.status_code == 202

    response = client.get(
        "/products/analytics/categories"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    category_a = next(
        item
        for item in data
        if item["category"] == "A"
    )

    assert category_a["count"] == 2


def test_price_distribution(client, admin_token):
    csv = (
        "name,price,category,brand\n"
        "P1,10,A,X\n"
        "P2,20,B,X\n"
        "P3,30,C,X\n"
        "P4,100,D,X"
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

    assert import_response.status_code == 202

    response = client.get(
        "/products/analytics/price-distribution?bins=3"
    )

    assert response.status_code == 200

    data = response.json()

    total = sum(
        item["count"]
        for item in data
    )

    assert total == 4