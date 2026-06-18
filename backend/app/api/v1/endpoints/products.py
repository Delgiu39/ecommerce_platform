from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_superuser
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.repositories.product import (
    get_product,
    get_products,
    create_product,
    update_product,
    delete_product,
)

router = APIRouter()

@router.get("/", response_model=List[ProductRead])
async def read_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Recupera l'elenco dei prodotti nel catalogo.
    """
    products = await get_products(db, skip=skip, limit=limit, active_only=active_only)
    return products

@router.get("/{product_id}", response_model=ProductRead)
async def read_product_by_id(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Recupera i dettagli di un singolo prodotto tramite ID.
    """
    product = await get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_new_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_active_superuser) # Note: User model needs to be imported or we can omit type hint / import it from app.models.user
):
    """
    Crea un nuovo prodotto. Endpoint riservato agli amministratori.
    """
    return await create_product(db, product_in=product_in)

@router.put("/{product_id}", response_model=ProductRead)
async def update_existing_product(
    product_id: UUID,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_active_superuser)
):
    """
    Aggiorna un prodotto esistente. Endpoint riservato agli amministratori.
    """
    product = await get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return await update_product(db, db_obj=product, product_in=product_in)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_active_superuser)
):
    """
    Rimuove fisicamente un prodotto dal catalogo. Endpoint riservato agli amministratori.
    """
    success = await delete_product(db, product_id=product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return

