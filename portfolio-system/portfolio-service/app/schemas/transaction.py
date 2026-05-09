from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.transaction import TransactionType, TransactionStatus


class TransactionCreate(BaseModel):
    type: TransactionType
    symbol: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Decimal
    idempotency_key: Optional[str] = None


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: TransactionType
    symbol: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Decimal
    status: TransactionStatus
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    limit: int
    offset: int


class PortfolioSummary(BaseModel):
    user_id: str
    total_invested: Decimal
    total_withdrawn: Decimal
    net_position: Decimal
    transaction_count: int
    last_updated: str
