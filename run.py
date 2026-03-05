# coding=utf-8

from datetime import datetime, timedelta

import asyncio
from pydantic import Field
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
    days: int | None = Field(
        default=None,
        description=(
            "only scrape advertisements published in the last N days. "
            "This parameter is ignored if 'after_date' is set."
        ),
    )
    ignore_existing: bool = Field(
        default=False,
        description="do not skip advertisements that were already collected before",
    )

    def model_post_init(self, _, /) -> None:
        """
        Prepare 'after_date' parameter.
        """

        if self.after_date is None:
            if self.days is not None:
                # Calculate 'after_date' based on 'days'
                self.after_date = datetime.now(tz=config.tz) - timedelta(days=self.days)

        elif self.after_date.tzinfo is None:
            # Convert to configured timezone
            self.after_date = self.after_date.astimezone(tz=config.tz)


if __name__ == "__main__":
    # Parse CLI arguments
    settings = Settings()

    # Run the main function in an asynchronous event loop
    asyncio.run(
        scrap_advertisements(
            after_date=settings.after_date,
            ignore_existing=settings.ignore_existing,
        )
    )
