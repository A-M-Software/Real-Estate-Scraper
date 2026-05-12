# coding=utf-8

from datetime import datetime

from .clients import ALL_CLIENTS, ClientName
from .advertisment import Advertisement, save_advertisements, load_advertisements
from .telegram import send_advertisements
from .logger import base_logger as logger


async def scrap_advertisements(
        after_date: datetime | None = None,
        ignore_existing: bool = False,
        only: list[ClientName] | None = None,
        send: bool = True,
        resend: bool = True,
        ids: list[int] | None = None,
) -> None:
    """
    Collect advertisements from all sources.
    """

    advertisements: list[Advertisement] = []

    if ids:
        # Collect advertisements from data file
        logger.info(f"Collecting advertisements from data files to resend")
        advertisements = load_advertisements(ids=ids)

        for id_ in ids:
            for advertisement in advertisements:
                if advertisement.id == id_:
                    # Found
                    break
            else:
                # Not found
                logger.warning(f"ID={id_} not found in data file")
    else:
        # Collect from clients
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

        if resend:
            # Collect failed advertisements as well
            logger.info(f"Collecting advertisements that failed to be sent to Telegram")

            if missed := load_advertisements(missing=True):
                # Found
                logger.warning(
                    f"Found {len(missed)} advertisements that failed "
                    f"to be sent to Telegram, adding to sending list",
                )
                advertisements.extend(missed)

        # Sort by published date
        advertisements.sort(key=lambda adv: adv.published_at)

        # Save collected advertisements to the file
        save_advertisements(advertisements=advertisements)

    if send:
        # Send collected advertisements to Telegram
        await send_advertisements(advertisements=advertisements)
