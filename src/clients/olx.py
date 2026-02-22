# coding=utf-8

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

    async def get_latest_advertisements(self) -> list[Advertisement]:
        """
        Get advertisements from the OLX.
        """

        pass
