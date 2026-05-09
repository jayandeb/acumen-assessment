from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.notification import Notification
from app.models.preference import NotificationPreference
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.schemas.preference import PreferenceUpdate, PreferenceResponse, PreferenceListResponse
from app.core.logger import logger

router = APIRouter()


def get_user_id(x_user_id: str = Header(...)) -> UUID:
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-ID header")


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    user_id: UUID = Depends(get_user_id),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    count_result = await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    notifications = result.scalars().all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
    )


@router.put("/preferences", response_model=PreferenceResponse)
async def upsert_preference(
    payload: PreferenceUpdate,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> PreferenceResponse:
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.channel == payload.channel,
        )
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.enabled = payload.enabled
        pref.min_amount = payload.min_amount
    else:
        pref = NotificationPreference(
            user_id=user_id,
            channel=payload.channel,
            enabled=payload.enabled,
            min_amount=payload.min_amount,
        )
        db.add(pref)

    await db.commit()
    await db.refresh(pref)
    logger.info("preference_updated", user_id=str(user_id), channel=payload.channel.value)
    return PreferenceResponse.model_validate(pref)


@router.get("/preferences", response_model=PreferenceListResponse)
async def list_preferences(
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> PreferenceListResponse:
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    preferences = result.scalars().all()
    return PreferenceListResponse(
        items=[PreferenceResponse.model_validate(p) for p in preferences]
    )
