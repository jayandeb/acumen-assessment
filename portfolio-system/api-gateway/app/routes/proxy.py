import httpx
from fastapi import APIRouter, Request, Response

from app.core.config import settings
from app.core.logger import logger

router = APIRouter()


async def _proxy(request: Request, target_url: str) -> Response:
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    headers["X-User-ID"] = getattr(request.state, "user_id", "")
    headers["X-Trace-ID"] = getattr(request.state, "trace_id", "")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body(),
            params=request.query_params,
        )

    logger.info(
        "proxied_request",
        method=request.method,
        target=target_url,
        status=response.status_code,
    )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


@router.api_route(
    "/portfolio/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy_portfolio(path: str, request: Request) -> Response:
    target = f"{settings.PORTFOLIO_SERVICE_URL}/{path}"
    return await _proxy(request, target)


@router.api_route(
    "/notifications/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy_notifications_path(path: str, request: Request) -> Response:
    target = f"{settings.NOTIFICATION_SERVICE_URL}/notifications/{path}"
    return await _proxy(request, target)


@router.api_route("/notifications", methods=["GET", "POST"])
async def proxy_notifications_root(request: Request) -> Response:
    target = f"{settings.NOTIFICATION_SERVICE_URL}/notifications"
    return await _proxy(request, target)


@router.api_route("/preferences", methods=["GET", "PUT", "POST"])
async def proxy_preferences(request: Request) -> Response:
    target = f"{settings.NOTIFICATION_SERVICE_URL}/preferences"
    return await _proxy(request, target)
