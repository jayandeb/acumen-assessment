import uuid
import enum

from sqlalchemy import Column, String, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"


class NotificationStatus(str, enum.Enum):
    SENT = "SENT"
    FAILED = "FAILED"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    transaction_id = Column(UUID(as_uuid=True), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.SENT)
    created_at = Column(DateTime(timezone=True), server_default="now()")
