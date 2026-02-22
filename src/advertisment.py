# coding=utf-8

from datetime import datetime
from dataclasses import dataclass
from locale import setlocale, LC_TIME


@dataclass
class Advertisement:
    # Apartment info
    city: str
    street: str
    building_name: str | None
    rooms: int
    area: int  # Square meters
    description: str

    # Basic info
    id: int
    url: str
    published_at: datetime
    source: str

    # Price
    price: float
    currency: str
    price_per_sqm: bool = False  # If True, price is per square meter, otherwise total price

    # Images
    photo_url: str | None = None

    @property
    def formatted_text(self) -> str:
        """
        Format advertisement information into a Telegram message
        """

        def _fmt_price(value: float | int) -> str:
            """
            Format given price with saved currency
            """

            return f"${value}" if self.currency.lower() in ("usd", "$") else f"{value} {self.currency}"

        # Heading

        text = f"<b>{self.street}, {self.city}</b>"

        if self.building_name:
            # Add to heading
            text += f" <b>({self.building_name})</b>"

        text += "\n"

        # Rooms, area

        text += f"{self.rooms}-кімнатна квартира, {self.area}м²\n"

        # Price

        if self.price_per_sqm:
            # Calculate total price
            price = self.price * self.area if self.area else None
            price_per_sqm = self.price

        else:
            # Calculate price per square meter
            price = self.price
            price_per_sqm = round(self.price / self.area, 1) if self.area else None

        if price and price_per_sqm:
            # Add both total price and price per square meter
            text += f"{_fmt_price(price)} ({_fmt_price(price_per_sqm)} за м²)"

        elif price:
            # Only total price
            text += f"{_fmt_price(price)}"

        elif price_per_sqm:
            # Only price per square meter
            text += f"{_fmt_price(price_per_sqm)} за м²"

        text += "\n"

        # Published at

        setlocale(LC_TIME, "uk_UA.UTF-8")  # Set locale to Ukrainian for date formatting
        text += f"Опубліковано: " + self.published_at.strftime("%d %B, %H:%M") + "\n"

        # Description

        if self.description:
            # Add description (truncated if too long)
            text += f"\n<i>{self.description[:197] + '...' if len(self.description) > 200 else self.description}</i>"

        return text
