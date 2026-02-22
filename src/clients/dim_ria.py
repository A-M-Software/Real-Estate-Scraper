# coding=utf-8

from inspect import signature

from .base import BaseClient
from ..advertisment import Advertisement
from ..logger import dim_ria_logger
from ..config import config


IntParam = int | list[int] | None


class DimRiaClient(BaseClient):
    """
    Client for interacting with the Dim.Ria API.
    """

    # Overload required attributes
    logger = dim_ria_logger
    config = config.dim_ria
    api_url = "https://developers.ria.com/dom"

    @classmethod
    def _init_params(cls) -> dict:
        """
        Prepare params for initializing HTTP client.
        """

        return {
            "params": {
                "api_key": cls.config.api_key,
            },
        }

    async def search_advertisements(
            self,
            page: int = 0,
            sort: str = "pub_d",  # Publication date (descending)
            category: IntParam = None,
            realty_type: IntParam = None,
            operation: IntParam = None,
            state_id: IntParam = None,
            city_id: IntParam = None,
            price_from: int | None = None,  # USD
            price_to: int | None = None,  # USD
            characteristics: dict[int, IntParam] | None = None,
            **kwargs: dict,
    ) -> dict:
        """
        Perform a request to the Dim.Ria API to search for advertisements.
        https://docs-developers.ria.com/en/dim_ria/search_advertisements
        """

        # Prepare characteristics parameters
        params = {
            f"characteristic[{key}]": value
            for key, value in (characteristics or {}).items()
            if value
        }

        for key in signature(self.search_advertisements).parameters.keys():
            if (value := locals()[key]) and key not in ("characteristics", "kwargs"):
                # Add parameter
                params[key] = value

        return await self.request_json(
            method="GET",
            url="/search",
            params=params,
            **kwargs,
        )

    async def get_advertisement(self, advertisement_id: int) -> dict:
        """
        Perform a request to the Dim.Ria API to get an advertisement by its ID.
        https://docs-developers.ria.com/en/dim_ria/advertisement_info
        """

        return await self.request_json(
            method="GET",
            url=f"/info/{advertisement_id}",
        )

    async def get_latest_advertisements(self) -> list[Advertisement]:
    @classmethod
    def _to_advertisement(cls, data: dict) -> Advertisement:
        """
        Convert raw data from the Dim.Ria API to an Advertisement object.
        """

        return Advertisement(
            # Apartment info
            city=data.get("city_name_uk"),
            street=data.get("street_name_uk"),
            building_name=data.get("user_newbuild_name_uk"),
            rooms=data.get("rooms_count"),
            area=data.get("total_square_meters"),
            description=" ".join(data["description_uk"].split()) if data.get("description_uk") else "",

            # Basic info
            id=data.get("realty_id"),
            url=(cls.public_url + data["beautiful_url"]) if data.get("beautiful_url") else None,
            published_at=datetime.fromtimestamp(data["publishing_date_ts"]),
            source="Dim.Ria",

            # Price
            price=data.get("price"),
            currency=data.get("currency_type"),
            price_per_sqm=data.get("price_type") == "за квадрат",

            # Images
            photo_url=(cls.cdn_url + data["main_photo"].replace(".jpg", "xl.jpg")) if data.get("main_photo") else None,
        )
        """
        Get latest advertisements from the Dim.Ria.
        """

        pass
