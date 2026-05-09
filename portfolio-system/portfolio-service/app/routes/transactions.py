from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    PortfolioSummary,
)
from app.services import transaction as transaction_service

router = APIRouter()


def get_user_id(x_user_id: str = Header(...)) -> UUID:
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-ID header")


def get_trace_id(x_trace_id: str = Header(default="unknown")) -> str:
    return x_trace_id


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    payload: TransactionCreate,
    user_id: UUID = Depends(get_user_id),
    trace_id: str = Depends(get_trace_id),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    return await transaction_service.create_transaction(db, user_id, payload, trace_id)


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    user_id: UUID = Depends(get_user_id),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    return await transaction_service.list_transactions(db, user_id, limit, offset)


@router.get("/summary", response_model=PortfolioSummary)
async def get_summary(
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> PortfolioSummary:
    return await transaction_service.get_summary(db, user_id)
