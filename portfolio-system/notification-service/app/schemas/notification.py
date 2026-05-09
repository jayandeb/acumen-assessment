from uuid import UUID
from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationStatus


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    transaction_id: UUID
    channel: NotificationChannel
    message: str
    status: NotificationStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
