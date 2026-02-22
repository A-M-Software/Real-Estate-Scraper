# coding=utf-8

from datetime import datetime

import asyncio
from pydantic_settings import BaseSettings

from src.main import scrap_advertisements


class Settings(BaseSettings, cli_parse_args=True):
    """
    CLI arguments for the script.
    """
    after_date: datetime | None = None


if __name__ == "__main__":
    # Parse CLI arguments
    settings = Settings()

    # Run the main function in an asynchronous event loop
    asyncio.run(
        scrap_advertisements(
            after_date=settings.after_date,
        )
    )
