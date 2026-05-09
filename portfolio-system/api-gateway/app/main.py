import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.logger import configure_logging, logger
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import limiter
from app.routes import auth, proxy

configure_logging()

app = FastAPI(title="API Gateway", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(AuthMiddleware)


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "api-gateway"}


app.include_router(auth.router)
app.include_router(proxy.router)
