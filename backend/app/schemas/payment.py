from decimal import Decimal
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: Decimal
    currency: str

class PaymentRead(BaseModel):
    id: UUID
    order_id: UUID
    stripe_payment_intent_id: str
    stripe_charge_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
