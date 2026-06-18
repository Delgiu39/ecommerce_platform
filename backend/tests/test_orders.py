import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_products import get_admin_token, get_user_token

@pytest.mark.anyio
async def test_order_creation_and_access_control(client: AsyncClient, db: AsyncSession):
    # 1. Setup Admin e Prodotto
    admin_token = await get_admin_token(client, db, "admin_order@example.com")
    prod_resp = await client.post(
        "/api/v1/products/",
        json={"name": "Test Product", "description": "Desc", "price": 100.00, "stock": 10},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    product_id = prod_resp.json()["id"]

    # 2. Setup Utenti
    token_a = await get_user_token(client, "usera@example.com")
    token_b = await get_user_token(client, "userb@example.com")

    # 3. Creazione Ordine Valido (3 unità) da parte di Utente A
    order_resp = await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": product_id, "quantity": 3}]},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert order_resp.status_code == 201
    order = order_resp.json()
    order_id = order["id"]
    assert order["status"] == "pending"
    assert order["total_amount"] == "300.00"

    # 4. Verifica decremento stock (deve essere 7)
    check_prod = await client.get(f"/api/v1/products/{product_id}")
    assert check_prod.json()["stock"] == 7

    # 5. Tentativo di ordinare una quantità maggiore dello stock disponibile (es. 8)
    fail_order_resp = await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": product_id, "quantity": 8}]},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert fail_order_resp.status_code == 400
    assert "Stock insufficiente" in fail_order_resp.json()["detail"]

    # 6. Utente B tenta di accedere all'ordine di Utente A (Atteso: 403 Forbidden)
    forbidden_resp = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert forbidden_resp.status_code == 403

    # 7. Utente A accede al proprio ordine (Atteso: 200 OK)
    ok_resp = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert ok_resp.status_code == 200
    assert ok_resp.json()["id"] == order_id

    # 8. Admin accede all'ordine di Utente A (Atteso: 200 OK)
    admin_ok_resp = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_ok_resp.status_code == 200
    assert admin_ok_resp.json()["id"] == order_id
