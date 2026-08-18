from fastapi import status


def test_register_first_user_becomes_admin(client):
    """First user should be assigned the admin role."""

    resp = client.post(
        "/auth/register",
        json={
            "email": "first@test.com",
            "password": "pass12345",
        },
    )

    assert resp.status_code == status.HTTP_201_CREATED

    token = resp.json()["access_token"]

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

    assert first.status_code == 201

    second = client.post(
        "/auth/register",
        json={
            "email": "b@test.com",
            "password": "pass12345",
        },
    )

    assert second.status_code == 201

    token = second.json()["access_token"]

    me = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert me.status_code == 200
    assert me.json()["role"] == "readonly"


def test_login_success(client):

    register = client.post(
        "/auth/register",
        json={
            "email": "login@test.com",
            "password": "pass12345",
        },
    )

    assert register.status_code == 201

    resp = client.post(
        "/auth/login",
        json={
            "email": "login@test.com",
            "password": "pass12345",
        },
    )

    assert resp.status_code == status.HTTP_200_OK
    assert "access_token" in resp.json()


def test_login_wrong_password(client):

    register = client.post(
        "/auth/register",
        json={
            "email": "fail@test.com",
            "password": "pass12345",
        },
    )

    assert register.status_code == 201

    resp = client.post(
        "/auth/login",
        json={
            "email": "fail@test.com",
            "password": "wrongpass",
        },
    )

    assert resp.status_code == status.HTTP_401_UNAUTHORIZED