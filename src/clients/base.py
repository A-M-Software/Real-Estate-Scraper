# coding=utf-8

from abc import ABC, abstractmethod
from logging import Logger

from ..advertisment import Advertisement


class BaseClient(ABC):
    """
    Base class for all clients.
    """

    logger: Logger

    @abstractmethod
    async def get_latest_advertisements(self) -> list[Advertisement]:
        """
        Get advertisements from the source.
        """

        pass
