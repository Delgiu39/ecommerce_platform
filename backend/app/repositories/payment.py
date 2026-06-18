from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.payment import Payment
from app.models.order import Order
from app.models.product import Product

async def create_payment(
    db: AsyncSession,
    order_id: UUID,
    stripe_payment_intent_id: str,
    amount: Decimal,
    currency: str,
    status: str
) -> Payment:
    """
    Registra un tentativo di pagamento nel database correlato a un ordine.
    """
    db_obj = Payment(
        order_id=order_id,
        stripe_payment_intent_id=stripe_payment_intent_id,
        amount=amount,
        currency=currency,
        status=status
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_payment_by_intent_id(db: AsyncSession, payment_intent_id: str) -> Payment | None:
    """
    Recupera un record di pagamento tramite l'ID del Payment Intent di Stripe.
    """
    result = await db.execute(
        select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id)
    )
    return result.scalars().first()

async def update_payment_status(
    db: AsyncSession,
    payment_intent_id: str,
    status: str,
    stripe_charge_id: str | None = None
) -> Payment | None:
    """
    Aggiorna lo stato di un pagamento e, di conseguenza, lo stato dell'ordine associato.
    Se il pagamento va a buon fine, l'ordine diventa 'paid'.
    Se il pagamento fallisce, l'ordine diventa 'failed' e lo stock dei prodotti viene ripristinato.
    """
    # 1. Recuperiamo il pagamento
    payment = await get_payment_by_intent_id(db, payment_intent_id)
    if not payment:
        return None

    # Se lo stato è già lo stesso, evitiamo elaborazioni ridondanti
    if payment.status == status:
        return payment

    # Aggiorniamo lo stato del pagamento
    payment.status = status
    if stripe_charge_id:
        payment.stripe_charge_id = stripe_charge_id
    db.add(payment)

    # 2. Recuperiamo l'ordine collegato
    order_result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == payment.order_id)
    )
    order = order_result.scalars().first()

    if order:
        if status == "succeeded":
            order.status = "paid"
            db.add(order)
        elif status in ["failed", "canceled"]:
            # Se l'ordine non era già contrassegnato come fallito/cancellato, ripristiniamo lo stock
            if order.status not in ["paid", "failed", "canceled"]:
                order.status = "failed"
                db.add(order)
                
                # Ripristino dello stock per ciascun prodotto nell'ordine
                for item in order.items:
                    product_result = await db.execute(
                        select(Product).where(Product.id == item.product_id)
                    )
                    product = product_result.scalars().first()
                    if product:
                        product.stock += item.quantity
                        db.add(product)

    await db.commit()
    await db.refresh(payment)
    return payment
