from uuid import UUID
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

async def get_product(db: AsyncSession, product_id: UUID) -> Product | None:
    """
    Recupera un singolo prodotto per ID.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalars().first()

async def get_products(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = True
) -> Sequence[Product]:
    """
    Recupera una lista di prodotti con paginazione. 
    Se active_only è True, restituisce solo i prodotti attivi.
    """
    query = select(Product)
    if active_only:
        query = query.where(Product.is_active == True)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def create_product(db: AsyncSession, product_in: ProductCreate) -> Product:
    """
    Crea un nuovo prodotto nel catalogo.
    """
    db_obj = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        image_url=product_in.image_url,
        is_active=product_in.is_active
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_product(
    db: AsyncSession, 
    db_obj: Product, 
    product_in: ProductUpdate
) -> Product:
    """
    Aggiorna i campi di un prodotto esistente.
    """
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def delete_product(db: AsyncSession, product_id: UUID) -> bool:
    """
    Rimuove fisicamente un prodotto dal database.
    Nota: fallirà se ci sono relazioni (es. ordini) a causa di ON DELETE RESTRICT.
    """
    db_obj = await get_product(db, product_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True
