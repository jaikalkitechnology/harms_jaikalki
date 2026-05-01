from redis.asyncio import Redis, from_url

from app.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis


async def ping_redis() -> bool:
    return await get_redis().ping()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
