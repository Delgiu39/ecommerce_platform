import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_superuser"] is False
    assert data["is_active"] is True
    assert "id" in data

@pytest.mark.anyio
async def test_register_invalid_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 422

@pytest.mark.anyio
async def test_register_short_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 422

@pytest.mark.anyio
async def test_register_privilege_escalation(client: AsyncClient):
    # Inviamo is_superuser=True, l'applicazione deve ignorarlo o rifiutarlo, ma in ogni caso l'utente deve essere creato come is_superuser=False
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "securepassword123",
            "full_name": "Test User",
            "is_superuser": True
        }
    )
    # Pydantic potrebbe rifiutare is_superuser ritornando 422 (poiché lo schema UserCreate non ha is_superuser), oppure potrebbe ignorarlo e ritornare 201.
    # In entrambi i casi il test passa poiché l'escalation viene mitigata.
    if response.status_code == 201:
        data = response.json()
        assert data["is_superuser"] is False
    else:
        assert response.status_code == 422

@pytest.mark.anyio
async def test_login_success(client: AsyncClient):
    # Prima registriamo
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
    )
    # Poi eseguiamo login (OAuth2 password form usa x-www-form-urlencoded)
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "user@example.com",
            "password": "securepassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.anyio
async def test_read_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

@pytest.mark.anyio
async def test_read_me_authorized(client: AsyncClient):
    # 1. Registra
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
    )
    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "user@example.com",
            "password": "securepassword123"
        }
    )
    token = login_resp.json()["access_token"]
    
    # 3. Leggi profilo /me
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["is_superuser"] is False
