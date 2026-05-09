from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logger import configure_logging, logger
from app.routes import health, notifications

configure_logging()

app = FastAPI(title="Notification Service", version="1.0.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router)
app.include_router(notifications.router)
