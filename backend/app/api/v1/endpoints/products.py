from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_products():
    return {"message": "Lista dei prodotti (Stub)"}
