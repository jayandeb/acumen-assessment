from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logger import logger
from app.models.auth import LoginRequest, TokenResponse, RefreshRequest

router = APIRouter(prefix="/auth")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS: dict[str, dict] = {}


def _load_users() -> None:
    seed_users = [
        {
            "email": "jayanta@test.com",
            "password": "password123",
            "user_id": "00000000-0000-0000-0000-000000000001",
        },
        {
            "email": "testuser@test.com",
            "password": "password123",
            "user_id": "00000000-0000-0000-0000-000000000002",
        },
    ]
    for u in seed_users:
        USERS[u["email"]] = {
            "user_id": u["user_id"],
            "hashed_password": pwd_context.hash(u["password"]),
        }


_load_users()


def _create_token(user_id: str, token_type: str, expire_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expire_delta
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": token_type},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    user = USERS.get(payload.email)
    if not user or not pwd_context.verify(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = _create_token(
        user["user_id"], "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = _create_token(
        user["user_id"], "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    logger.info("user_logged_in", user_id=user["user_id"], email=payload.email)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest) -> TokenResponse:
    try:
        decoded = jwt.decode(
            payload.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        user_id = decoded.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    access_token = _create_token(
        user_id, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh = _create_token(
        user_id, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)
