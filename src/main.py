# coding=utf-8

from datetime import datetime

from .clients import ALL_CLIENTS
from .advertisment import Advertisement
from .telegram import send_advertisements
from .logger import base_logger as logger


async def scrap_advertisements(after_date: datetime | None = None) -> None:
    """
    Collect advertisements from all sources.
    """

    advertisements: list[Advertisement] = []

    for Client in ALL_CLIENTS:
        try:
            async with Client() as client:
                # Collect advertisements from the client and extend the list
                advertisements.extend(
                    await client.get_latest_advertisements(after_date=after_date),
                )

        except (Exception, ValueError):
            # Failed
            logger.error(
                f"Failed to collect advertisements from {Client.__name__}",
                exc_info=True,
            )

    # Send collected advertisements to Telegram
    await send_advertisements(advertisements=advertisements)
