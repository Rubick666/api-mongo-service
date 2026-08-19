from fastapi import status


def test_register_first_user_becomes_admin(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "first@test.com",
            "password": "pass12345",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text

    token = response.json()["access_token"]

    me = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert me.status_code == status.HTTP_200_OK
    assert me.json()["role"] == "admin"


def test_register_second_user_becomes_readonly(client):
    first = client.post(
        "/auth/register",
        json={
            "email": "a@test.com",
            "password": "pass12345",
        },
    )

    assert first.status_code == status.HTTP_201_CREATED, first.text

    second = client.post(
        "/auth/register",
        json={
            "email": "b@test.com",
            "password": "pass12345",
        },
    )

    assert second.status_code == status.HTTP_201_CREATED, second.text

    token = second.json()["access_token"]

    me = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert me.status_code == status.HTTP_200_OK
    assert me.json()["role"] == "readonly"


def test_login_success(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "login@test.com",
            "password": "pass12345",
        },
    )

    assert register.status_code == status.HTTP_201_CREATED, register.text

    response = client.post(
        "/auth/login",
        json={
            "email": "login@test.com",
            "password": "pass12345",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "fail@test.com",
            "password": "pass12345",
        },
    )

    assert register.status_code == status.HTTP_201_CREATED, register.text

    response = client.post(
        "/auth/login",
        json={
            "email": "fail@test.com",
            "password": "wrongpass",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED