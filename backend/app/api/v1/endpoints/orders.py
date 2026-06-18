from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead
from app.repositories import order as order_repo

router = APIRouter()

@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_new_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_in: OrderCreate,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Crea un nuovo ordine per l'utente corrente.
    Valida lo stock ed esegue il decremento a magazzino.
    """
    try:
        db_order = await order_repo.create_order(
            db=db, user_id=current_user.id, order_in=order_in
        )
        return db_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[OrderRead])
async def list_user_orders(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Restituisce l'elenco degli ordini dell'utente corrente.
    """
    orders = await order_repo.get_orders_for_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return orders

@router.get("/{order_id}", response_model=OrderRead)
async def read_order_details(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Recupera i dettagli di un ordine specifico.
    L'utente può vedere solo i propri ordini, a meno che non sia superuser.
    """
    order = await order_repo.get_order(db=db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordine non trovato"
        )
    if order.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non si dispone dei privilegi necessari per visualizzare questo ordine"
        )
    return order
