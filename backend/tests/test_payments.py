import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_products import get_admin_token, get_user_token

@pytest.mark.anyio
async def test_payments_flow_and_simulation_security(client: AsyncClient, db: AsyncSession):
    # 1. Setup Admin, Utente A e Prodotto
    admin_token = await get_admin_token(client, db, "admin_pay@example.com")
    token_a = await get_user_token(client, "usera_pay@example.com")
    
    prod_resp = await client.post(
        "/api/v1/products/",
        json={"name": "Test Product Pay", "description": "Desc", "price": 100.00, "stock": 10},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    product_id = prod_resp.json()["id"]

    # 2. Utente A crea un primo ordine per 2 unità (Disponibili: 10, rimanenti: 8)
    order_resp = await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": product_id, "quantity": 2}]},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert order_resp.status_code == 201
    order1 = order_resp.json()
    order1_id = order1["id"]

    # Verifica stock prodotto nel DB (deve essere 8)
    prod_check = await client.get(f"/api/v1/products/{product_id}")
    assert prod_check.json()["stock"] == 8

    # 3. Creazione Payment Intent per l'Ordine 1
    pi_resp = await client.post(
        f"/api/v1/payments/create-intent/{order1_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert pi_resp.status_code == 201
    pi_data = pi_resp.json()
    assert "client_secret" in pi_data
    assert "payment_intent_id" in pi_data
    payment_intent1_id = pi_data["payment_intent_id"]

    # 4. Verifica blocco di simulate-webhook senza autenticazione
    anon_sim = await client.post(
        f"/api/v1/payments/simulate-webhook?payment_intent_id={payment_intent1_id}&event_type=succeeded"
    )
    assert anon_sim.status_code in [401, 403]

    # 5. Verifica blocco di simulate-webhook per utente non admin
    user_sim = await client.post(
        f"/api/v1/payments/simulate-webhook?payment_intent_id={payment_intent1_id}&event_type=succeeded",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert user_sim.status_code == 403

    # 6. Simulazione successo pagamento da parte dell'Admin
    admin_sim = await client.post(
        f"/api/v1/payments/simulate-webhook?payment_intent_id={payment_intent1_id}&event_type=succeeded",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_sim.status_code == 200
    assert admin_sim.json()["payment_status"] == "succeeded"

    # Verifica che lo stato dell'ordine 1 sia passato a "paid"
    order1_check = await client.get(
        f"/api/v1/orders/{order1_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert order1_check.json()["status"] == "paid"

    # 7. Utente A crea un secondo ordine per 3 unità (Disponibili: 8, ordinati: 3 -> stock nel DB: 5)
    order2_resp = await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": product_id, "quantity": 3}]},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert order2_resp.status_code == 201
    order2 = order2_resp.json()
    order2_id = order2["id"]

    prod_check2 = await client.get(f"/api/v1/products/{product_id}")
    assert prod_check2.json()["stock"] == 5

    # Creazione Payment Intent per l'ordine 2
    pi2_resp = await client.post(
        f"/api/v1/payments/create-intent/{order2_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert pi2_resp.status_code == 201
    payment_intent2_id = pi2_resp.json()["payment_intent_id"]

    # 8. Simuliamo un pagamento fallito (failed) tramite webhook simulato dall'Admin
    admin_sim_failed = await client.post(
        f"/api/v1/payments/simulate-webhook?payment_intent_id={payment_intent2_id}&event_type=failed",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_sim_failed.status_code == 200
    assert admin_sim_failed.json()["payment_status"] == "failed"

    # Verifica che lo stato dell'ordine 2 sia passato a "failed"
    order2_check = await client.get(
        f"/api/v1/orders/{order2_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert order2_check.json()["status"] == "failed"

    # 9. Verifica ripristino stock dopo fallimento pagamento (deve tornare a 8: 5 + 3 = 8)
    prod_final = await client.get(f"/api/v1/products/{product_id}")
    assert prod_final.json()["stock"] == 8
