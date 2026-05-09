from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    PortfolioSummary,
)
from app.services.cache import get_portfolio_summary, set_portfolio_summary, invalidate_portfolio_summary
from app.tasks.publisher import celery_app


async def create_transaction(
    db: AsyncSession,
    user_id: UUID,
    payload: TransactionCreate,
    trace_id: str,
) -> TransactionResponse:
    if payload.idempotency_key:
        result = await db.execute(
            select(Transaction).where(Transaction.idempotency_key == payload.idempotency_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("idempotent_transaction_returned", idempotency_key=payload.idempotency_key)
            return TransactionResponse.model_validate(existing)

    transaction = Transaction(
        user_id=user_id,
        type=payload.type,
        symbol=payload.symbol,
        quantity=payload.quantity,
        price=payload.price,
        amount=payload.amount,
        status=TransactionStatus.COMPLETED,
        idempotency_key=payload.idempotency_key,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    await invalidate_portfolio_summary(str(user_id))

    event_data = {
        "event_type": "TRANSACTION_CREATED",
        "trace_id": trace_id,
        "transaction_id": str(transaction.id),
        "user_id": str(user_id),
        "type": transaction.type.value,
        "symbol": transaction.symbol,
        "quantity": str(transaction.quantity) if transaction.quantity else None,
        "price": str(transaction.price) if transaction.price else None,
        "amount": str(transaction.amount),
        "created_at": transaction.created_at.isoformat(),
    }
    celery_app.send_task("process_notification_event", args=[event_data], queue="notifications")
    logger.info(
        "transaction_created",
        transaction_id=str(transaction.id),
        user_id=str(user_id),
        trace_id=trace_id,
    )

    return TransactionResponse.model_validate(transaction)


async def list_transactions(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
) -> TransactionListResponse:
    count_result = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_summary(
    db: AsyncSession,
    user_id: UUID,
) -> PortfolioSummary:
    cached = await get_portfolio_summary(str(user_id))
    if cached:
        logger.info("portfolio_summary_cache_hit", user_id=str(user_id))
        return PortfolioSummary(**cached)

    result = await db.execute(
        select(Transaction).where(Transaction.user_id == user_id)
    )
    transactions = result.scalars().all()

    total_invested = Decimal("0")
    total_withdrawn = Decimal("0")
    for t in transactions:
        if t.type.value in ("BUY", "DEPOSIT"):
            total_invested += t.amount
        else:
            total_withdrawn += t.amount

    summary = PortfolioSummary(
        user_id=str(user_id),
        total_invested=total_invested,
        total_withdrawn=total_withdrawn,
        net_position=total_invested - total_withdrawn,
        transaction_count=len(transactions),
        last_updated=datetime.now(timezone.utc).isoformat(),
    )
    await set_portfolio_summary(str(user_id), summary.model_dump(mode="json"))
    logger.info("portfolio_summary_cache_miss", user_id=str(user_id))
    return summary
