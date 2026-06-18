import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User

async def get_admin_token(client: AsyncClient, db: AsyncSession, email: str = "admin@example.com") -> str:
    # Registra utente
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepassword123", "full_name": "Admin User"}
    )
    # Promuovi ad admin nel DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    user.is_superuser = True
    db.add(user)
    await db.commit()
    
    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "securepassword123"}
    )
    return login_resp.json()["access_token"]

async def get_user_token(client: AsyncClient, email: str = "user@example.com") -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepassword123", "full_name": "Normal User"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "securepassword123"}
    )
    return login_resp.json()["access_token"]

@pytest.mark.anyio
async def test_read_products_empty(client: AsyncClient):
    response = await client.get("/api/v1/products/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.anyio
async def test_create_product_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/products/",
        json={
            "name": "Super Phone",
            "description": "A great phone",
            "price": 499.99,
            "stock": 10
        }
    )
    assert response.status_code == 401

@pytest.mark.anyio
async def test_create_product_forbidden_for_normal_user(client: AsyncClient):
    token = await get_user_token(client)
    response = await client.post(
        "/api/v1/products/",
        json={
            "name": "Super Phone",
            "description": "A great phone",
            "price": 499.99,
            "stock": 10
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

@pytest.mark.anyio
async def test_product_crud_lifecycle_admin(client: AsyncClient, db: AsyncSession):
    token = await get_admin_token(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create product
    create_resp = await client.post(
        "/api/v1/products/",
        json={
            "name": "Super Phone",
            "description": "A great phone",
            "price": 499.99,
            "stock": 10
        },
        headers=headers
    )
    assert create_resp.status_code == 201
    product = create_resp.json()
    product_id = product["id"]
    assert product["name"] == "Super Phone"
    assert product["price"] == "499.99"
    assert product["stock"] == 10
    
    # 2. Read product details
    detail_resp = await client.get(f"/api/v1/products/{product_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == "Super Phone"
    
    # 3. Update product
    update_resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={
            "price": 399.99,
            "stock": 5
        },
        headers=headers
    )
    assert update_resp.status_code == 200
    updated_prod = update_resp.json()
    assert updated_prod["price"] == "399.99"
    assert updated_prod["stock"] == 5
    
    # 4. Delete product
    delete_resp = await client.delete(f"/api/v1/products/{product_id}", headers=headers)
    assert delete_resp.status_code == 204
    
    # 5. Verify deleted
    verify_resp = await client.get(f"/api/v1/products/{product_id}")
    assert verify_resp.status_code == 404
