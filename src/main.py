# coding=utf-8

from datetime import datetime

from .clients import ALL_CLIENTS, ClientName
from .advertisment import Advertisement, save_advertisements
from .telegram import send_advertisements
from .logger import base_logger as logger


async def scrap_advertisements(
        after_date: datetime | None = None,
        ignore_existing: bool = False,
        only: list[ClientName] | None = None,
) -> None:
    """
    Collect advertisements from all sources.
    """

    advertisements: list[Advertisement] = []

    for Client in ALL_CLIENTS:
        if only is not None and Client.name not in only:
            # Ignore this client
            continue

        try:
            # Iterate each client
            logger.info(f"Collecting advertisements from {Client.__name__} ({after_date=}, {ignore_existing=})")

            async with Client() as client:
                # Collect advertisements from the client and extend the list
                advertisements.extend(
                    await client.get_latest_advertisements(
                        after_date=after_date,
                        ignore_existing=ignore_existing,
                    ),
                )

        except (Exception, ValueError):
            # Failed
            logger.error(
                f"Failed to collect advertisements from {Client.__name__}",
                exc_info=True,
            )

    # Sort by published date
    advertisements.sort(key=lambda adv: adv.published_at)

    # Save collected advertisements to the file
    save_advertisements(advertisements=advertisements)

    # Send collected advertisements to Telegram
    await send_advertisements(advertisements=advertisements)
