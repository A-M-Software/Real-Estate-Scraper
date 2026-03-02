import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.config import config
from src.employee_stats.bot.handlers import router
from src.logger import bot_logger as logger


def build_bot() -> Bot:
    """
    Create configured bot instance.
    """

    return Bot(
        token=config.telegram.token,
        default=DefaultBotProperties(
            parse_mode="HTML",
            link_preview_is_disabled=True,
        ),
    )


async def main() -> None:
    """
    Entry point: register router and start polling.
    """

    logger.info("🚀 Starting Telegram bot...")

    bot = build_bot()
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
