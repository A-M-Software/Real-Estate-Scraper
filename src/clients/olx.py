# coding=utf-8

import re
from lxml import html

from datetime import datetime, date

from .base import BaseClient
from ..advertisment import Advertisement
from ..logger import olx_logger
from ..config import config


_MONTHS = {
    "січня": 1,
    "лютого": 2,
    "березня": 3,
    "квітня": 4,
    "травня": 5,
    "червня": 6,
    "липня": 7,
    "серпня": 8,
    "вересня": 9,
    "жовтня": 10,
    "листопада": 11,
    "грудня": 12,
}


class OLXClient(BaseClient):
    """
    Client for interacting with the OLX.
    """

    # Overload required attributes
    logger = olx_logger
    config = config.olx

    # URLs
    api_url = "https://www.olx.ua"
    search_url = "/uk/nedvizhimost/kvartiry/prodazha-kvartir/chernovtsy/"

    @classmethod
    def _init_params(cls) -> dict:
        """
        Initialize parameters for the OLX client.
        """

        return {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0",
            },
        }

    def _parse_searched_advertisement(self, advertisement: html.HtmlElement) -> dict:
        """
        Parse advertisement from the search results page,
        and returns a dictionary with `id`, `url`, `published_at` and `is_promoted` fields.
        """

        # Prepare variables
        today = date.today()

        # Parse advertisement's details
        advertisement_id, = advertisement.xpath("@id")  # type: str
        url, *_ = advertisement.xpath(".//a/@href")  # type: str

        # Check if required fields are found
        assert advertisement_id is not None, "Advertisement ID not found"
        assert url is not None, "Advertisement URL not found"

        if url.startswith("/"):
            # Add the base URL if the URL is relative
            url = self.api_url + url

        # Check if the advertisement is promoted
        is_promoted = url.endswith("promoted")

        # Parse publication date
        published_str, = advertisement.xpath(".//p[@data-testid=\"location-date\"]//text()")  # type: str
        assert published_str, "Publication date not found"
        published_str = published_str.split(" - ")[-1]

        if match := re.match(r"Сьогодні о (?P<time>\d\d:\d\d)", published_str):
            # Advertisement published today => parse hour & minute
            time_str = match.group("time")
            published_at = datetime.strptime(time_str, "%H:%M")
            published_at = published_at.replace(year=today.year, month=today.month, day=today.day)

        elif match := re.match(r"(?P<day>\d{1,2}) (?P<month>[А-Яа-я]+) (?P<year>\d{4}) р.", published_str):
            # Advertisement published on a specific date => parse day, month & year
            day = int(match.group("day"))
            year = int(match.group("year"))
            month = _MONTHS[match.group("month").lower()]
            published_at = datetime(year=year, month=month, day=day)

        else:
            # Unknown date format
            raise ValueError(f"Unknown date format: {published_str!r}")

        return {
            "id": advertisement_id,
            "url": url,
            "published_at": published_at,
            "is_promoted": is_promoted,
        }

    async def search_advertisements(self, **params) -> list[dict]:
        """
        Search for latest advertisements on the OLX, and returns a list of objects.
        Each object contains `id`, `url`, `published_at` and `is_promoted` fields.
        """

        # Set list view for parsing
        params["view"] = "list"

        # Request page
        response = await self.request_html(
            method="GET",
            url=self.search_url,
            params=params,
        )

        # Parse all advertisements from the page
        tree = html.fromstring(response)
        advertisements: list[html.HtmlElement] = tree.xpath("//div[contains(@data-cy, \"l-card\")]")

        # Prepare for parsing
        self.logger.debug(f"Found {len(advertisements)} advertisements to parse")
        items = []

        for index, advertisement in enumerate(advertisements, start=1):
            try:
                # Parse advertisement's details
                item = self._parse_searched_advertisement(advertisement)

            except (ValueError, Exception) as error:
                # Failed to parse
                self.logger.error(
                    f"({index}/{len(advertisements)}) "
                    f"Failed to parse advertisement",
                    exc_info=True,
                )

            else:
                # Add parsed item to the list
                items.append(item)

                self.logger.debug(
                    f"({index}/{len(advertisements)}) "
                    f"Successfully parsed advertisement: {item}"
                )

        # Sort by publication date (most recent first)
        items.sort(key=lambda i: i["published_at"], reverse=True)

        return items

    async def get_latest_advertisements(self, after_date: datetime | None = None) -> list[Advertisement]:
        """
        Get advertisements from the OLX.
        """

        self.logger.info(f"Getting latest advertisements from OLX")

        # Prepare variables
        advertisements: list[Advertisement] = []
        existing_ids: set[int] = self.data.get("existing_ids") or set()
        self.data.setdefault("existing_ids", set())

        # Prepare parameters for searching
        kwargs = {
            "currency": "USD",
            "search[private_business]": "private",  # Only owner
            "search[order]": "created_at:desc",  # Publication date (descending)
        }

        # Load advertisements
        data = await self.search_advertisements(**kwargs)
        index = 0

        for index, item in enumerate(data):
            if item["id"] in existing_ids:
                # Found an existing advertisement, stop loading more
                self.logger.info(f"Found an existing ID={item['id']}, stop loading more")
                break

            elif after_date is not None and item["published_at"] < after_date:
                # Found an advertisement published before the specified date, stop loading more
                self.logger.info(f"Found an ID posted before '{after_date}', stop loading more")
                break

        # Limit to only new advertisements
        data = data[:index]
