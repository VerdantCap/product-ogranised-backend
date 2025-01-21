from typing import AsyncIterator

import redis.asyncio as redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.retry import Retry

from config import settings

retry = Retry(ExponentialBackoff(), 6)
decode_redis_pool = redis.BlockingConnectionPool(  # type: ignore
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    max_connections=20,
    timeout=20,
    password=settings.REDIS_PASSWORD,
    retry=retry,
    retry_on_error=[BusyLoadingError, ConnectionError, TimeoutError],
    connection_class=redis.Connection
    if not settings.REDIS_TLS
    else redis.SSLConnection,
)


async def redis_context() -> AsyncIterator[redis.StrictRedis]:
    redis_client = redis.StrictRedis(connection_pool=decode_redis_pool)
    try:
        yield redis_client
    finally:
        await redis_client.close()
