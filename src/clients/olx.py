# coding=utf-8

import re
from lxml import html

from datetime import datetime, date, timezone

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
    name = "OLX"
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
        tz = timezone.utc  # Page is loaded in UTC timezone (and converted to local on front-end), so we have UTC here

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
            published_at = published_at.replace(year=today.year, month=today.month, day=today.day, tzinfo=tz)
            published_at_date = False

        elif match := re.match(r"(?P<day>\d{1,2}) (?P<month>[А-Яа-я]+) (?P<year>\d{4}) р.", published_str):
            # Advertisement published on a specific date => parse day, month & year
            day = int(match.group("day"))
            year = int(match.group("year"))
            month = _MONTHS[match.group("month").lower()]
            published_at = datetime(year=year, month=month, day=day, tzinfo=tz)
            published_at_date = True

        else:
            # Unknown date format
            raise ValueError(f"Unknown date format: {published_str!r}")

        return {
            "id": advertisement_id,
            "url": url,
            "published_at": published_at,
            "published_at_date": published_at_date,
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

            except (ValueError, Exception):
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

    async def get_advertisement(self, url: str) -> str:
        """
        Get advertisement's page from the OLX by URL.
        """

        return await self.request_html(method="GET", url=url)

    @classmethod
    def _to_advertisement(cls, text: str, item: dict) -> Advertisement:
        """
        Parse advertisement's page and returns an `Advertisement` object.
        Also, requires helper `item` object to get `id`, `url` and `published_at` fields.
        """

        def get_property(name: str) -> str | None:
            """
            Get value for given property (if any).
            Otherwise, returns None.
            """

            for property_ in properties:
                if property_.startswith(name + ": "):
                    # Found property => get value
                    return property_.split(name + ": ")[-1]

        def check_property(name: str) -> bool:
            """
            Check if property with given name exists
            """

            for property_ in properties:
                if name in property_.split(":")[0]:
                    # Found property => return True
                    return True

            return False

        def clean(value: str) -> str | None:
            """
            Removes extra spaces from the value (if it's not None).
            """

            return " ".join(value.split()) if value else None

        # Parse advertisement's page
        tree = html.fromstring(text)

        # Split blocks
        main, = tree.xpath("//div[@data-testid=\"main\"]")
        side, = tree.xpath("//div[@data-testid=\"aside\"]")
        properties: list[str] = main.xpath(".//div[@data-testid=\"ad-parameters-container\"]/p/text()")
        properties = [clean(p) for p in properties if p.split()]

        # City
        city, *_ = side.xpath(".//p[text()=\"Місцезнаходження\"]/../div//p[1]/text()") + [None]  # type: str

        # Street (can't get street from OLX, so using advertisement title
        street, *_ = side.xpath(".//div[@data-cy=\"offer_title\"]//h4/text()") + [None]  # type: str

        # Building name
        building_name = get_property("Назва ЖК")

        # Rooms
        if rooms := get_property("Кількість кімнат"):
            # Get only number
            rooms = rooms.split()[0]

        if area := get_property("Загальна площа"):
            # Get only number
            area = int(float(area.split()[0]))

        if floor := get_property("Поверх"):
            # Convert to number
            floor = int(floor)

        if total_floors := get_property("Поверховість"):
            # Convert to number
            total_floors = int(total_floors)

        # Check if marked as allowed
        brokers_allowed = check_property("Готовий співпрацювати з ріелторами")

        # Description
        description = "\n".join(map(clean, main.xpath(".//div[@data-testid=\"ad_description\"]//div/text()")))

        # Price
        price_str, = side.xpath(".//div[@data-testid=\"ad-price-container\"]//h3/text()")  # type: str
        price_str, currency = price_str.rsplit(maxsplit=1)
        price = int(float(price_str.replace(" ", "")))

        # Images
        photo_url, *_ = main.xpath(".//div[@data-testid=\"ad-photo\"]//img/@src") + [None]  # type: str

        return Advertisement(
            # Apartment info
            city=clean(city),
            street=clean(street),
            building_name=building_name,  # Already cleaned in property
            rooms=rooms,
            area=area,
            floor=floor,
            total_floors=total_floors,
            description=description,  # Already cleaned

            # Basic info
            id=item["id"],
            url=item["url"],
            published_at=item["published_at"],
            published_at_date=item["published_at_date"],
            source=cls.name,
            brokers_allowed=brokers_allowed,

            # Price
            price=price,
            currency=currency,
            price_per_sqm=False,

            # Images
            photo_url=photo_url,

            # Internal
            data=text,
        )

    async def get_latest_advertisements(
            self,
            after_date: datetime | None = None,
            ignore_existing: bool = False,
    ) -> list[Advertisement]:
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
            if item["id"] in existing_ids and not ignore_existing:
                # Found an existing advertisement, stop loading more
                self.logger.info(f"Found an existing ID={item['id']}, stop loading more")
                break

            elif after_date is not None and item["published_at"] < after_date and not item["is_promoted"]:
                # Found an advertisement published before the specified date, stop loading more
                self.logger.info(f"Found an ID posted before '{after_date}', stop loading more")
                break

        # Limit to only new advertisements
        self.logger.info(f"Limiting to {index} new advertisement(s) (excluding existing and old ones)")
        data = data[:index]

        for duplicate_index, duplicate_item in reversed(list(enumerate(data))):
            for check_index, check_item in enumerate(data[:duplicate_index]):
                if duplicate_item["id"] == check_item["id"]:
                    # Found a duplicate ID => remove it
                    self.logger.debug(f"Found a duplicate ID={check_item['id']}, removing it")
                    data.pop(duplicate_index)
                    break

        self.logger.info(f"Loading info for {len(data)} advertisement(s)")

        for index, item in enumerate(data, start=1):
            # Load each advertisement
            advertisement_id = item["id"]
            url = item["url"]

            try:
                # Load advertisement's details
                text = await self.get_advertisement(url=url)
                advertisement = self._to_advertisement(text=text, item=item)

            except OverflowError:
                # Too many requests, stop loading more advertisements
                self.logger.error(
                    f"({index}/{len(data)}) "
                    f"Too many requests while loading advertisement ID={advertisement_id}, stopping",
                )
                break

            except (ValueError, Exception):
                # Failed
                self.logger.error(
                    f"({index}/{len(data)}) "
                    f"Failed to load data for advertisement ID={advertisement_id}",
                    exc_info=True,
                )

            else:
                # Success
                advertisements.append(advertisement)

            # Save ID to data
            self.data["existing_ids"].add(advertisement_id)

        self.logger.info(f"Successfully collected {len(advertisements)}/{len(data)} advertisements")

        return advertisements
