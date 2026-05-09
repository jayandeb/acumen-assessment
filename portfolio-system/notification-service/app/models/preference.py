import uuid

from sqlalchemy import Column, Boolean, Numeric, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.models.notification import Base, NotificationChannel


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel = Column(Enum(NotificationChannel), nullable=False)
    enabled = Column(Boolean, default=True)
    min_amount = Column(Numeric(18, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now()")
