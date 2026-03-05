# coding=utf-8

from datetime import datetime

import asyncio
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from src.config import config
from src.main import scrap_advertisements


class Settings(BaseSettings, cli_parse_args=True):
    """
    CLI arguments for the script.
    """

    after_date: datetime | None = Field(
        default=None,
        description=(
            "only scrape advertisements published after this date. "
            "If timezone is not explicitly set, treating it as the configured timezone."
        ),
    )

    @field_validator("after_date")
    @classmethod
    def set_timezone(cls, after_date: datetime | None):
        """
        Set timezone for 'after_date'.
        """

        if after_date and after_date.tzinfo is None:
            # Convert from UTC to configured timezone
            after_date = after_date.astimezone(tz=config.tz)

        return after_date


if __name__ == "__main__":
    # Parse CLI arguments
    settings = Settings()

    # Run the main function in an asynchronous event loop
    asyncio.run(
        scrap_advertisements(
            after_date=settings.after_date,
        )
    )
