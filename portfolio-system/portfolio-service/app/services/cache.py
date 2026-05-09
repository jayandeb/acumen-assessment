import json

import redis.asyncio as aioredis

from app.core.config import settings

CACHE_TTL = 300
SUMMARY_KEY_PREFIX = "portfolio_summary"


async def get_portfolio_summary(user_id: str) -> dict | None:
    r = aioredis.from_url(settings.REDIS_URL)
    key = f"{SUMMARY_KEY_PREFIX}:{user_id}"
    cached = await r.get(key)
    await r.aclose()
    if cached:
        return json.loads(cached)
    return None


async def set_portfolio_summary(user_id: str, summary: dict) -> None:
    r = aioredis.from_url(settings.REDIS_URL)
    key = f"{SUMMARY_KEY_PREFIX}:{user_id}"
    await r.setex(key, CACHE_TTL, json.dumps(summary))
    await r.aclose()


async def invalidate_portfolio_summary(user_id: str) -> None:
    r = aioredis.from_url(settings.REDIS_URL)
    key = f"{SUMMARY_KEY_PREFIX}:{user_id}"
    await r.delete(key)
    await r.aclose()
