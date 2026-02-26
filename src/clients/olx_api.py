# coding=utf-8

from datetime import datetime, timedelta

from .base import BaseClient
from ..advertisment import Advertisement
from ..logger import olx_logger
from ..config import config


class OLXAPIClient(BaseClient):
    """
    Client for interacting with the OLX API.
    """

    # Overload required attributes
    name = "OLX"
    logger = olx_logger
    config = config.olx

    # URLs
    api_url = "https://api.olx.ua/api/partner"
    token_url = "https://api.olx.ua/api/open/oauth/token"

    @classmethod
    def _init_params(cls) -> dict:
        """
        Initialize parameters for the OLX client.
        """

        return {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0",
                "Version": "2.0",
            },
        }

    async def request_json(self, method: str, url: str, ignore_auth: bool = False, **kwargs) -> dict:
        """
        Perform a request with given parameters and authorization.
        Returns JSON response.
        """

        if not ignore_auth:
            # Set authorization header with access token
            kwargs.setdefault("headers", {})
            kwargs["headers"]["Authorization"] = f"Bearer {await self.access_token}"

        return await super().request_json(
            method=method,
            url=url,
            **kwargs,
        )

    @property
    async def access_token(self) -> str:
        """
        Get access token for the OLX API.
        """

        if access_token := self.data.get("access_token"):
            if expires_at := self.data.get("access_token_expires_at"):
                if expires_at > datetime.now():
                    # Valid access token exists, return it
                    return access_token

            # Expired
            self.logger.info("Access token expired")

        else:
            # No access token found
            self.logger.info("No access token found")

        # No valid access token, request a refresh
        return await self._refresh_tokens()

    @property
    def refresh_token(self) -> str:
        """
        Get refresh token for the OLX API.
        """

        return self.data.get("refresh_token") or self.config.api_key

    async def _refresh_tokens(self) -> str:
        """
        Request new access and refresh tokens using the refresh token.
        Store the new tokens and their expiration time in the client's data for future use.
        Return the new access token.
        """

        self.logger.info(f"Refreshing tokens for OLX API")

        # Request token
        response = await self.request_json(
            method="POST",
            url=self.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
            },
            ignore_auth=True,
        )

        # Update tokens
        self.data["refresh_token"] = response["refresh_token"]
        self.data["access_token"] = response["access_token"]
        self.data["access_token_expires_at"] = datetime.now() + timedelta(seconds=response["expires_in"])

        return response["access_token"]

    async def get_latest_advertisements(self, after_date: datetime | None = None) -> list[Advertisement]:
        """
        Get advertisements from the OLX.
        """

        return []
