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
    published_at: datetime

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

        # Heading

        text = f"<b>{self.street}, {self.city}</b>"

        if self.building_name:
            # Add to heading
            text += f" <b>({self.building_name})</b>"

        text += "\n"

        # Rooms, area

        text += f"{self.rooms}-кімнатна квартира, {self.area}м²\n"

        # Price

        text += f"${self.price}" if self.currency.lower() in ("usd", "$") else f"{self.price} {self.currency}"

        if self.price_per_sqm:
            # Add per square meter info
            text += " за м²"

        text += "\n"

        # Published at

        setlocale(LC_TIME, "uk_UA.UTF-8")  # Set locale to Ukrainian for date formatting
        text += f"Опубліковано: " + self.published_at.strftime("%d %B, %H:%M") + "\n"

        # Description

        if self.description:
            # Add description (truncated if too long)
            text += f"\n{self.description[:197] + '...' if len(self.description) > 200 else self.description}"

        return text
