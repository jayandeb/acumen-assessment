from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.models.notification import NotificationChannel


class PreferenceUpdate(BaseModel):
    channel: NotificationChannel
    enabled: bool
    min_amount: Decimal = Decimal("0")


class PreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    channel: NotificationChannel
    enabled: bool
    min_amount: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class PreferenceListResponse(BaseModel):
    items: List[PreferenceResponse]
