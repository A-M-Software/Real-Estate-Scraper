# coding=utf-8

import pickle
from typing import Self
from logging import Logger
from types import TracebackType
from abc import ABC, abstractmethod

from httpx import AsyncClient, HTTPError

from ..config import BaseClientConfig
from ..advertisment import Advertisement


class BaseClient(AsyncClient, ABC):
    """
    Base class for all clients.
    """

    logger: Logger
    config: BaseClientConfig
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

        # Initialize data & create directory if needed
        self.data = None
        self.config.data_file.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _init_params(cls) -> dict:
        """
        Prepare params for initializing HTTP client.
        """

        return {}

    async def __aenter__(self) -> Self:
        """
        Enter the async context manager.
        """

        self.data = self._load_data()

        await super().__aenter__()
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None = None,
            exc_value: BaseException | None = None,
            traceback: TracebackType | None = None,
    ) -> None:
        """
        Exit the async context manager.
        """

        await super().__aexit__(exc_type, exc_value, traceback)

        with self.config.data_file.open("wb") as data_file:
            # Save data to file
            pickle.dump(self.data, data_file)

    def _dump_data(self, data: dict) -> None:
        """
        Write data to file.
        """

        self.logger.debug(f"Dumping data to {self.config.data_file}")

        try:
            with self.config.data_file.open("wb") as data_file:
                # Save data to file
                pickle.dump(data, data_file)

        except (PermissionError, IOError, Exception):
            # Failed to dump data
            self.logger.error(f"Failed to dump data to {self.config.data_file}", exc_info=True)

    def _load_data(self) -> dict:
        """
        Read data from file.
        """

        self.logger.debug(f"Loading data from {self.config.data_file}")

        try:
            with self.config.data_file.open("rb") as data_file:
                # Load data from file
                return pickle.load(data_file)

        except (PermissionError, FileNotFoundError, IOError, EOFError):
            # Unable to open data file or empty data
            self.logger.warning(f"Unable to load data from {self.config.data_file}, returning empty data")
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
