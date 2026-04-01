# coding=utf-8

from asyncio import sleep
from aiogram import Bot
from aiogram.enums import ParseMode

from .config import config
from .logger import telegram_logger as logger
from .advertisment import Advertisement, save_advertisements


async def send_advertisements(
        advertisements: list[Advertisement],
        chat_id: int = config.telegram.chat_id,
        token: str = config.telegram.token,
        ignore_sent: bool = False,
        **kwargs,
) -> None:
    """
    Send given advertisements to configured Telegram channel.
    """

    if not advertisements:
        # Nothing to send
        logger.info("No advertisements to send to Telegram")
        return

    logger.info(f"Sending {len(advertisements)} advertisements to Telegram channel {chat_id}")

    # Initialize Telegram bot
    bot = Bot(token=token)

    for advertisement in advertisements:
        if advertisement.chat_id == chat_id and advertisement.message_id is not None:
            if not ignore_sent:
                # Already was sent to telegram
                logger.warning(
                    f"Advertisement ID={advertisement.id} (source={advertisement.source}) "
                    f"already was sent to {chat_id=} (message_id={advertisement.message_id}), skipping"
                )
                continue

        # Send each advertisement to Telegram channel
        await send_advertisement(advertisement, bot, chat_id, **kwargs)

        # Save updated advertisements with message IDs to the file
        save_advertisements(advertisements=advertisements)

        # Sleep for a short time to avoid hitting Telegram API rate limits
        await sleep(2)


async def send_advertisement(advertisement: Advertisement, bot: Bot, chat_id: int, **kwargs) -> None:
    """
    Send a single advertisement to Telegram channel.
    """

    logger.info(
        f"Sending advertisement ID={advertisement.id} (source={advertisement.source}) "
        f"to Telegram channel {chat_id}"
    )

    if advertisement.photo_url:
        # Send as photo
        message = await bot.send_photo(
            chat_id=chat_id,
            photo=advertisement.photo_url,
            caption=advertisement.formatted_text,
            parse_mode=ParseMode.HTML,
            **kwargs,
        )

    else:
        # Send as text
        message = await bot.send_message(
            chat_id=chat_id,
            text=advertisement.formatted_text,
            parse_mode=ParseMode.HTML,
            **kwargs,
        )

    # Save message ID to the advertisement for future reference
    advertisement.chat_id = chat_id
    advertisement.message_id = message.message_id
