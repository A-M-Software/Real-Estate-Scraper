# coding=utf-8

from abc import ABC, abstractmethod
from logging import Logger

from pydantic import BaseModel
from httpx import AsyncClient, HTTPError

from ..advertisment import Advertisement


class BaseClient(AsyncClient, ABC):
    """
    Base class for all clients.
    """

    logger: Logger
    config: BaseModel
    api_url: str = ""
    default_timeout: int = 16

    def __init__(self) -> None:
        """
        Initialize client for making API requests.
        """

        super().__init__(
            base_url=self.api_url,
            timeout=self.default_timeout,
            **self._init_params(),
        )

    @classmethod
    def _init_params(cls) -> dict:
        """
        Prepare params for initializing HTTP client.
        """

        return {}

    async def request_json(self, method: str, url: str, **kwargs) -> dict:
        """
        Perform a request with given parameters.
        Returns JSON response.
        """

        self.logger.debug(f"Performing {method} {url} request ({kwargs})")

        try:
            # Make a request & check status
            response = await self.request(
                method=method,
                url=url,
                **kwargs,
            )
            response.raise_for_status()

            # Parse JSON
            data = response.json()

        except HTTPError as error:
            # Request failed
            self.logger.error(f"Failed to perform {method} {url} request", exc_info=True)
            raise error

        except (ValueError, Exception) as error:
            # Probably failed to parse JSON
            self.logger.error(f"Failed to parse JSON response from {method} {url} request", exc_info=True)
            raise error

        else:
            # Log success
            self.logger.debug(f"Successfully performed {method} {url} request")

        return data


    @abstractmethod
    async def get_latest_advertisements(self) -> list[Advertisement]:
        """
        Get advertisements from the source.
        """

        pass
