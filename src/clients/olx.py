# coding=utf-8

from .base import BaseClient
from ..advertisment import Advertisement
from ..logger import olx_logger


class OLXClient(BaseClient):
    """
    Client for interacting with the OLX API.
    """

    logger = olx_logger

    async def get_latest_advertisements(self) -> list[Advertisement]:
        """
        Get advertisements from the OLX.
        """

        pass
