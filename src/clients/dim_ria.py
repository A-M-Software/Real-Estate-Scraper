# coding=utf-8

from math import ceil
from datetime import datetime
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
    name = "Dim.Ria"
    logger = dim_ria_logger
    config = config.dim_ria

    # URLs
    api_url = "https://developers.ria.com/dom"
    cdn_url = "https://cdn.riastatic.com/photos/"  # For formatting image URLs
    public_url = "https://dom.ria.com/uk/"  # For formatting advertisement URLs

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
            floor=data.get("floor"),
            total_floors=data.get("floors_count"),
            description=" ".join(data["description_uk"].split()) if data.get("description_uk") else "",

            # Basic info
            id=data.get("realty_id"),
            url=(cls.public_url + data["beautiful_url"]) if data.get("beautiful_url") else None,
            published_at=datetime.fromtimestamp(data["publishing_date_ts"]),
            published_at_date=False,  # Not only date but time as well
            source=cls.name,
            brokers_allowed=False,  # Can't check

            # Price
            price=data.get("price"),
            currency=data.get("currency_type"),
            price_per_sqm=data.get("price_type") == "за квадрат",

            # Images
            photo_url=(cls.cdn_url + data["main_photo"].replace(".jpg", "xl.jpg")) if data.get("main_photo") else None,
        )

    async def _find_published_after(
            self,
            advertisement_ids: list[int],
            after_date: datetime,
    ) -> tuple[list[int], dict[int, dict]]:
        """
        Find the IDs of advertisements published after the specified date using binary search.
        Also, returns a dictionary with the data of the checked advertisements
        to avoid making additional requests for them later.
        """

        async def _get_publishing_date(advertisement_id: int) -> datetime:
            """
            Helper function to get the publishing date of an advertisement by its ID.
            """

            data = await self.get_advertisement(advertisement_id)
            checked[advertisement_id] = data  # Save data to checked dict
            return datetime.fromtimestamp(data["publishing_date_ts"])

        self.logger.debug(
            f"Binary searching for advertisements published after "
            f"{after_date} among {len(advertisement_ids)} IDs"
        )
        checked: dict[int, dict] = {}

        if await _get_publishing_date(advertisement_ids[0]) < after_date:
            # First ID is posted before => no matches
            return [], checked

        elif await _get_publishing_date(advertisement_ids[-1]) > after_date:
            # Latest ID is posted after => all matches
            return advertisement_ids, checked

        # Binary search for the first ID that is posted before the specified date
        left, right = 0, len(advertisement_ids) - 1

        while left < right:
            # Get middle index
            mid = (left + right) // 2

            if await _get_publishing_date(advertisement_ids[mid]) > after_date:
                # Posted later in list => need to check the right half
                left = mid + 1

            else:
                # Posted earlier in list => need to check the left half
                right = mid

        # All IDs before the first posted earlier than the specified date
        return advertisement_ids[:right], checked

    async def get_latest_advertisements(self, after_date: datetime | None = None) -> list[Advertisement]:
        """
        Get latest advertisements from the Dim.Ria.
        Using data files, check for already processed advertisements, and return only new ones.
        After processing, saves the IDs of the new advertisements to the data file.
        If ``after_date`` is provided, only advertisements published after the specified date will be returned.
        """

        self.logger.info(f"Getting latest advertisements from Dim.Ria")

        # Prepare variables
        advertisement_ids: list[int] = []
        checked_ids: set[int] = set()
        advertisements: list[Advertisement] = []
        existing_ids: set[int] = self.data.get("existing_ids") or set()
        self.data.setdefault("existing_ids", set())

        # Prepare parameters for searching
        kwargs = {
            "city_id": self.config.city_ids,
            "sort": "pub_d",  # Publication date (descending)
            "category": 1,  # Apartments
            "realty_type": 2,  # Apartments
            "operation": 1,  # Sale
            "characteristics": {
                1437: 1436,  # Only owner
            },
        }

        if existing_ids:
            # Process advertisements only before any of existing IDs
            self.logger.info(f"Using {len(existing_ids)} existing IDs to filter advertisements")

        elif after_date:
            # Process advertisements only after the specified date
            self.logger.info(f"Filtering out advertisements published after '{after_date}'")

        else:
            # Get all advertisements
            self.logger.info("No existing IDs or 'after_date' provided, getting all advertisements")

        # Load pages
        page = 0
        total_pages: int | None = None

        while (page := page + 1) <= (total_pages or 1):
            # Load each page
            self.logger.info(f"Loading page ({page}/{total_pages or '?'}) of advertisements")
            data = await self.search_advertisements(page=page - 1, **kwargs)

            if ids := data.get("items"):
                # Process IDs based on parameters
                if existing_ids:
                    # Add IDs until found
                    found = False

                    for advertisement_id in ids:
                        if advertisement_id in existing_ids:
                            # Found an existing ID, stop loading more pages
                            self.logger.info(
                                f"Found an existing ID={advertisement_id} on page {page}, "
                                f"stopping loading more pages",
                            )
                            found = True
                            break

                        advertisement_ids.append(advertisement_id)

                    if found:
                        # Stop loading more pages
                        break

                elif after_date:
                    # Add only IDs posted after the specified date to the list
                    after_ids, checked = await self._find_published_after(
                        advertisement_ids=ids,
                        after_date=after_date,
                    )
                    advertisement_ids.extend(after_ids)

                    for checked_id, advertisement in checked.items():
                        if checked_id in advertisement_ids:
                            # Save checked advertisements to the list (filter out unmatched ones)
                            advertisements.append(self._to_advertisement(advertisement))
                            checked_ids.add(checked_id)

                    if len(after_ids) < len(ids):
                        # No more on next pages, stop loading more pages
                        self.logger.info(
                            f"Found an ID posted before '{after_date}' on page {page}, "
                            f"stopping loading more pages",
                        )
                        break

                else:
                    # Add IDs to the list
                    advertisement_ids.extend(ids)

            if total_count := data.get("count"):
                # Calculate total pages
                total_pages = ceil(total_count / 100)  # 100 items per page
        else:
            # Finished loading pages
            self.logger.info(f"Found {len(advertisement_ids)} advertisement IDs, no more pages to load")

        self.logger.info(f"Loading info for {len(advertisement_ids)} advertisement(s)")
        advertisement_ids.sort(reverse=True)

        for index, advertisement_id in enumerate(advertisement_ids, start=1):
            if advertisement_id not in checked_ids:
                # Load each advertisement by ID
                self.logger.info(
                    f"({index}/{len(advertisement_ids)}) "
                    f"Loading advertisement ID={advertisement_id}"
                )

                try:
                    # Load advertisement data
                    data = await self.get_advertisement(advertisement_id)
                    advertisement = self._to_advertisement(data)

                except OverflowError:
                    # Too many requests, stop loading more advertisements
                    self.logger.error(
                        f"({index}/{len(advertisement_ids)}) "
                        f"Too many requests while loading advertisement ID={advertisement_id}, stopping",
                    )
                    break

                except (ValueError, Exception):
                    # Failed
                    self.logger.error(
                        f"({index}/{len(advertisement_ids)}) "
                        f"Failed to load data for advertisement ID={advertisement_id}",
                        exc_info=True,
                    )

                else:
                    # Success
                    advertisements.append(advertisement)

            else:
                # Skip already checked ID
                self.logger.info(
                    f"({index}/{len(advertisement_ids)}) "
                    f"Advertisement ID={advertisement_id} already processed, skipping",
                )

            # Save ID to data
            self.data["existing_ids"].add(advertisement_id)

        self.logger.info(f"Successfully collected {len(advertisements)}/{len(advertisement_ids)} advertisements")

        return advertisements
