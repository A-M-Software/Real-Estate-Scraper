# coding=utf-8

from datetime import datetime

from .base import BaseClient
from ..advertisment import Advertisement
from ..logger import olx_logger
from ..config import config


class OLXClient(BaseClient):
    """
    Client for interacting with the OLX API.
    """

    # Overload required attributes
    logger = olx_logger
    config = config.olx

    async def get_latest_advertisements(self, after_date: datetime | None = None) -> list[Advertisement]:
        """
        Get advertisements from the OLX.
        """

        return []
