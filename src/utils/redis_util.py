from typing import AsyncIterator
import logging
import redis.asyncio as redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.retry import Retry

from config import settings
logging.basicConfig(level=logging.DEBUG)

retry = Retry(ExponentialBackoff(), 6)
redis_pool = redis.BlockingConnectionPool(  # type: ignore
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    max_connections=20,
    timeout=20,
    password=settings.REDIS_PASSWORD,
    retry=retry,
    retry_on_error=[BusyLoadingError, ConnectionError, TimeoutError]
)


async def redis_context() -> AsyncIterator[redis.Redis]:
    redis_client = redis.Redis(connection_pool=redis_pool)
    try:
        yield redis_client
    finally:
        await redis_client.close()
