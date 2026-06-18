from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json
import uuid
import stripe

from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.payment import PaymentIntentResponse, PaymentRead
from app.repositories import order as order_repo
from app.repositories import payment as payment_repo

router = APIRouter()

@router.post("/create-intent/{order_id}", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Crea un Payment Intent di Stripe (o mockato) per l'ordine specificato.
    Valida che l'ordine appartenga all'utente ed sia ancora pendente.
    """
    # 1. Recuperiamo l'ordine
    order = await order_repo.get_order(db=db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordine non trovato"
        )

    # 2. Verifichiamo i permessi
    if order.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non si dispone dei privilegi necessari per questo ordine"
        )

    # 3. Verifichiamo lo stato dell'ordine
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossibile pagare un ordine in stato: '{order.status}'"
        )

    # 4. Creazione Payment Intent (Stripe vs Mock)
    currency = "eur"
    if settings.STRIPE_SECRET_KEY:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            # Stripe accetta gli importi espressi in centesimi (es. 10.00 EUR -> 1000)
            amount_cents = int(order.total_amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata={
                    "order_id": str(order.id),
                    "user_id": str(current_user.id)
                }
            )
            client_secret = intent.client_secret
            payment_intent_id = intent.id
            stripe_status = intent.status
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Errore di comunicazione con Stripe: {str(e)}"
            )
    else:
        # Modalità Mock locale se le chiavi non sono fornite
        payment_intent_id = f"mock_pi_{uuid.uuid4().hex[:16]}"
        client_secret = f"mock_cs_{uuid.uuid4().hex[:24]}"
        stripe_status = "requires_payment_method"

    # 5. Registriamo il tentativo di pagamento nel database
    await payment_repo.create_payment(
        db=db,
        order_id=order.id,
        stripe_payment_intent_id=payment_intent_id,
        amount=order.total_amount,
        currency=currency,
        status=stripe_status
    )

    return PaymentIntentResponse(
        client_secret=client_secret,
        payment_intent_id=payment_intent_id,
        amount=order.total_amount,
        currency=currency
    )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint per la ricezione asincrona delle conferme di pagamento (Webhook Stripe).
    Verifica la firma webhook in presenza di chiavi Stripe configurate.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    event = None
    # Se Stripe è configurato in produzione, la verifica della firma è strettamente obbligatoria
    if settings.STRIPE_SECRET_KEY:
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configurazione Stripe incompleta: manca STRIPE_WEBHOOK_SECRET"
            )
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signature header (stripe-signature) mancante. Firma obbligatoria in produzione."
            )
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload non valido")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firma webhook non valida")
    else:
        # Modalità Mock (solo per sviluppo locale in assenza di chiavi Stripe)
        try:
            event = json.loads(payload.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload JSON non valido")

    # Estraiamo i campi d'interesse dall'evento
    event_type = event.get("type") if isinstance(event, dict) else event.type
    event_data = event.get("data") if isinstance(event, dict) else event.data
    obj = event_data.get("object") if isinstance(event_data, dict) else event_data.object

    payment_intent_id = obj.get("id") if isinstance(obj, dict) else obj.id
    stripe_charge_id = obj.get("latest_charge") if isinstance(obj, dict) else getattr(obj, "latest_charge", None)

    if event_type == "payment_intent.succeeded":
        await payment_repo.update_payment_status(
            db=db,
            payment_intent_id=payment_intent_id,
            status="succeeded",
            stripe_charge_id=stripe_charge_id
        )
    elif event_type in ["payment_intent.payment_failed", "payment_intent.canceled"]:
        await payment_repo.update_payment_status(
            db=db,
            payment_intent_id=payment_intent_id,
            status="failed"
        )

    return {"status": "success"}

@router.post("/simulate-webhook")
async def simulate_stripe_webhook(
    *,
    db: AsyncSession = Depends(get_db),
    payment_intent_id: str,
    event_type: str,  # succeeded o failed
    charge_id: str = "mock_ch_12345",
    current_admin: User = Depends(deps.get_current_active_superuser)
):
    """
    Endpoint di utilità per test locali e simulazioni.
    Consente di attivare lo stato succeeded/failed di un pagamento senza passare da Stripe CLI.
    Richiede privilegi di amministratore.
    """
    if event_type == "succeeded":
        status_val = "succeeded"
    elif event_type == "failed":
        status_val = "failed"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo di evento simulato non supportato. Usa 'succeeded' o 'failed'"
        )

    payment = await payment_repo.update_payment_status(
        db=db,
        payment_intent_id=payment_intent_id,
        status=status_val,
        stripe_charge_id=charge_id if event_type == "succeeded" else None
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record di pagamento non trovato nel database"
        )

    return {"status": "success", "payment_status": payment.status}
