import uuid
import enum

from sqlalchemy import Column, String, Numeric, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    type = Column(Enum(TransactionType), nullable=False)
    symbol = Column(String(20), nullable=True)
    quantity = Column(Numeric(18, 8), nullable=True)
    price = Column(Numeric(18, 8), nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.COMPLETED)
    idempotency_key = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now()")
