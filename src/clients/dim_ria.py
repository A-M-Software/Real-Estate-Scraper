# coding=utf-8

from .base import BaseClient
from ..advertisment import Advertisement
from ..logger import dim_ria_logger


class DimRiaClient(BaseClient):
    """
    Client for interacting with the Dim.Ria API.
    """

    logger = dim_ria_logger

    async def get_latest_advertisements(self) -> list[Advertisement]:
        """
        Get advertisements from the Dim.Ria.
        """

        pass
