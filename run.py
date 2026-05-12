# coding=utf-8

from datetime import datetime, timedelta

import asyncio
from pydantic import Field
from pydantic_settings import BaseSettings, CliImplicitFlag

from src.config import config
from src.clients import ClientName
from src.main import scrap_advertisements


class Settings(BaseSettings, cli_parse_args=True, cli_kebab_case=True):
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
    ignore_existing: CliImplicitFlag[bool] = Field(
        default=False,
        description="do not skip advertisements that were already collected before",
    )
    send: CliImplicitFlag[bool] = Field(
        default=True,
        description="send advertisements to telegram",
    )
    resend: CliImplicitFlag[bool] = Field(
        default=True,
        description="resend advertisements that failed to be sent to telegram",
    )
    only: list[ClientName] | None = Field(
        default=None,
        description="Collect advertisements only from these sources. If not set, collect from all.",
    )
    ids: list[int] = Field(
        default=None,
        description=(
            "List of advertisement IDs to resend to Telegram, even if they were sent before. "
            "They will be collected from data file. If any ID is not found, it will be skipped."
        ),
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
            self.after_date = self.after_date.replace(tzinfo=config.tz)


if __name__ == "__main__":
    # Parse CLI arguments
    settings = Settings()

    # Run the main function in an asynchronous event loop
    asyncio.run(
        scrap_advertisements(
            after_date=settings.after_date,
            ignore_existing=settings.ignore_existing,
            only=settings.only,
            send=settings.send,
            resend=settings.resend,
            ids=settings.ids,
        )
    )
