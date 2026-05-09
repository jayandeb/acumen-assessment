from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logger import logger

SKIP_PATHS = {"/health", "/auth/login", "/auth/refresh", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(skip) for skip in SKIP_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            user_id = payload.get("sub")
            if not user_id:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token payload"},
                )
            request.state.user_id = user_id
        except JWTError as exc:
            logger.warning("jwt_validation_failed", error=str(exc), path=path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        return await call_next(request)
