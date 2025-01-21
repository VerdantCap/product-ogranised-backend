from datetime import datetime, timezone
from typing import Any, AsyncIterator

import aiohttp
import dateparser
from fastapi import Request
from tzlocal import get_localzone

from utils.constants import IPINFO_URL


def str_to_timestamp(time_str: str) -> float:
    parsed_time = dateparser.parse(time_str)
    if not parsed_time:
        raise ValueError("Failed to parse time string")
    return parsed_time.timestamp()


def str_to_utc_datetime(time_str: str) -> datetime:
    parsed_time = dateparser.parse(time_str)
    if not parsed_time:
        raise ValueError("Failed to parse time string")
    return parsed_time


async def get_timezone(request: Request) -> AsyncIterator[Any]:
    async with aiohttp.ClientSession() as session:
        if request.client:
            client_ip = request.client.host
            response = await session.get(IPINFO_URL.format(client_ip))
            data = await response.json()
            yield data.get("timezone") or get_localzone().key


def convert_to_utc_time_str(time_str: str) -> str:
    parsed_time = dateparser.parse(time_str)
    if not parsed_time:
        raise ValueError("Failed to parse time string")
    return parsed_time.isoformat()


def get_current_date() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc).replace(microsecond=0)
