# coding=utf-8

from aiogram import Bot

from .config import config
from .advertisment import Advertisement


async def send_advertisements(
        advertisements: list[Advertisement],
        chat_id: int = config.telegram.chat_id,
        token: str = config.telegram.token,
) -> None:
    """
    Send given advertisements to configured Telegram channel using.
    """

    # Initialize Telegram bot
    bot = Bot(token=token)

    for advertisement in advertisements:
        # Send each advertisement to Telegram channel
        await _send_advertisement(advertisement, bot, chat_id)


async def _send_advertisement(advertisement: Advertisement, bot: Bot, chat_id: int) -> None:
    """
    Send a single advertisement to Telegram channel.
    """

    # TODO: URL button

    if advertisement.photo_url:
        # Send as photo
        await bot.send_photo(
            chat_id=chat_id,
            photo=advertisement.photo_url,
            caption=advertisement.formatted_text,
        )

    else:
        # Send as text
        await bot.send_message(
            chat_id=chat_id,
            text=advertisement.formatted_text,
        )
