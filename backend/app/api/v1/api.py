from fastapi import APIRouter
from app.api.v1.endpoints import auth, products, orders, payments

api_router = APIRouter()

# Aggreghiamo tutti i router con i rispettivi prefissi e tag openapi
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticazione"])
api_router.include_router(products.router, prefix="/products", tags=["Prodotti"])
api_router.include_router(orders.router, prefix="/orders", tags=["Ordini"])
api_router.include_router(payments.router, prefix="/payments", tags=["Pagamenti"])
