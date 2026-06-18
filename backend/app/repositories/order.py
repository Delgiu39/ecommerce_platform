from uuid import UUID
from typing import Sequence
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate

async def get_order(db: AsyncSession, order_id: UUID) -> Order | None:
    """
    Recupera un singolo ordine per ID con tutti i suoi elementi pre-caricati.
    """
    result = await db.execute(
        select(Order)
        .options(joinedload(Order.items))
        .where(Order.id == order_id)
    )
    return result.scalars().first()

async def get_orders_for_user(
    db: AsyncSession, 
    user_id: UUID, 
    skip: int = 0, 
    limit: int = 100
) -> Sequence[Order]:
    """
    Recupera tutti gli ordini associati a un utente, ordinati per creazione decrescente,
    con gli elementi pre-caricati.
    """
    result = await db.execute(
        select(Order)
        .options(joinedload(Order.items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().unique().all()

async def create_order(db: AsyncSession, user_id: UUID, order_in: OrderCreate) -> Order:
    """
    Crea un nuovo ordine gestendo lo stock e i prezzi dei prodotti all'interno di una transazione.
    Solleva ValueError in caso di problemi di disponibilità o stock.
    """
    total_amount = Decimal("0.00")
    order_items = []

    # Iteriamo sui prodotti dell'ordine per validarli ed elaborare prezzi/stock
    for item in order_in.items:
        # Recuperiamo il prodotto dal database con un blocco riga per evitare race condition
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        product = product_result.scalars().first()

        if not product:
            raise ValueError(f"Prodotto con ID {item.product_id} non trovato")

        if not product.is_active:
            raise ValueError(f"Il prodotto '{product.name}' non è più attivo e non può essere acquistato")

        if product.stock < item.quantity:
            raise ValueError(
                f"Stock insufficiente per '{product.name}'. Richiesti: {item.quantity}, Disponibili: {product.stock}"
            )

        # Decrementiamo lo stock del prodotto
        product.stock -= item.quantity
        db.add(product)

        # Calcoliamo il costo parziale ed impostiamo lo storico del prezzo
        item_price = product.price
        total_amount += item_price * item.quantity

        order_item = OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            price_at_purchase=item_price
        )
        order_items.append(order_item)

    # Creiamo l'oggetto dell'ordine principale
    db_order = Order(
        user_id=user_id,
        total_amount=total_amount,
        status="pending",
        items=order_items
    )

    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)

    # Ricarichiamo l'ordine completo per assicurare che gli item siano visibili
    result = await db.execute(
        select(Order)
        .options(joinedload(Order.items))
        .where(Order.id == db_order.id)
    )
    return result.scalars().first()
