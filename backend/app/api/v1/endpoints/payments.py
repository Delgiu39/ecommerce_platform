from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_payments():
    return {"message": "Lista dei pagamenti (Stub)"}
