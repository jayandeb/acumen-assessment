from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional, Literal


class TransactionEvent(BaseModel):
    event_type: Literal["TRANSACTION_CREATED"]
    trace_id: str
    transaction_id: UUID
    user_id: UUID
    type: Literal["BUY", "SELL", "DEPOSIT", "WITHDRAWAL"]
    symbol: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Decimal
    created_at: datetime
