from decimal import Decimal
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0, description="La quantità acquistata deve essere maggiore di zero")

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1, description="L'ordine deve contenere almeno un prodotto")

class OrderItemRead(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    price_at_purchase: Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderRead(BaseModel):
    id: UUID
    user_id: UUID
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)
