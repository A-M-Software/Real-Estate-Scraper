import time
from typing import Any

from src.clients import OLXAPIClient

_cache_ts: float = 0.0
_cache_active: list[dict[str, Any]] | None = None


async def fetch_all_adverts() -> list[dict[str, Any]]:
    """
    Fetch all adverts from OLX API using pagination.

    Returns:
        A list of raw adverts as returned by the OLX API.
    """

    async with OLXAPIClient() as client:
        all_adverts: list[dict[str, Any]] = []
        offset = 0

        while True:
            payload = await client.request_json(
                method="GET",
                url="/adverts",
                params={"offset": offset},
            )

            adverts = payload.get("data") or []
            if not adverts:
                break

            all_adverts.extend(adverts)
            offset += 100  # Next page

    return all_adverts


def only_active(adverts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Filter only active adverts.

    Args:
        adverts: Raw adverts list.

    Returns:
        Only adverts where status == "active".
    """

    return [advert for advert in adverts if advert.get("status") == "active"]


async def get_active_cached() -> list[dict[str, Any]]:
    """
    Return active adverts with a simple in-process TTL cache.

    Cache is stored in module-level variables and is shared across calls
    within the same Python process.
    """

    global _cache_ts, _cache_active  # Cache storage

    now = time.time()
    if _cache_active is not None and (now - _cache_ts) < 60:
        return _cache_active

    active_adverts = only_active(await fetch_all_adverts())
    _cache_active = active_adverts
    _cache_ts = now

    return active_adverts
