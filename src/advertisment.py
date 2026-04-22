# coding=utf-8

import re
from json import load, dump
from datetime import datetime

from pydantic import BaseModel, Field
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .config import config

# Maximum length of description in Telegram message (to avoid exceeding Telegram limits)
_MAX_DESC_LENGTH = 512


class Advertisement(BaseModel):
    # Apartment info
    city: str
    street: str
    building_name: str | None = None
    rooms: int | str | None = None
    area: int | None = None  # Square meters
    floor: int | None = None
    total_floors: int | None = None
    description: str | None = None

    # Basic info
    id: int
    url: str
    published_at: datetime
    published_at_is_date: bool = False  # True if published_at contains only date information without time
    source: str
    brokers_allowed: bool = False

    # Price
    price: float
    currency: str = "$"
    price_per_sqm: bool = False  # If True, price is per square meter, otherwise total price

    # Images
    photo_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)
    video_urls: list[str] = Field(default_factory=list)

    # Internal
    chat_id: int | None = None
    message_id: int | None = None  # Telegram message ID after sending to Telegram channel
    collected_at: datetime = Field(default_factory=lambda: datetime.now(tz=config.tz))
    data: dict | str | None = None

    @property
    def formatted_text(self) -> str:
        """
        Format advertisement information into a Telegram message
        """

        # Heading

        text = f"📍 <b>{self.street}, {self.city}</b>"

        if self.building_name:
            # Add to heading
            text += f" <b>({self.building_name})</b>"

        text += "\n"

        # Rooms, area

        if self.rooms or self.area:
            text += f"🏠 "
            texts = []

            if self.rooms:
                sep = "-" if not str(self.rooms).endswith("+") else " "  # Support for "3+" rooms format
                texts.append(f"{self.rooms}{sep}кімнатна квартира")

            if self.area:
                texts.append(f"{self.area}м²")

            if self.total_floors:
                # Display both floor and total floors
                texts.append(f"поверх {self.floor or '?'}/{self.total_floors}")

            elif self.floor is not None:
                # Only floor is available
                texts.append(f"поверх {self.floor}")

            text += ", ".join(texts) + "\n"

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
            text += f"💰 {format_price(price, self.currency)} ({format_price(price_per_sqm, self.currency)} за м²)"

        elif price:
            # Only total price
            text += f"💰 {format_price(price, self.currency)}"

        elif price_per_sqm:
            # Only price per square meter
            text += f"💰 {format_price(price_per_sqm, self.currency)} за м²"

        text += "\n"

        # Published at

        if self.published_at:
            text += f"🕓 Опубліковано: "

            if self.published_at_is_date:
                # No time information, only date
                text += self.published_at.astimezone(config.tz).strftime("%d %B (%A)") + "\n"

            else:
                # Date and time information available
                text += self.published_at.astimezone(config.tz).strftime("%d %B (%A), %H:%M") + "\n"

        # Broker forbidden

        if self.brokers_allowed:
            # Marked as allowed
            text += "✅ Готовий співпрацювати з посередниками\n"

        elif self.brokers_forbidden:
            # Found words indicating that brokers are forbidden
            text += "🚫 Посередникам не турбувати\n"

        # Link & ID

        text += f"ℹ️ <a href=\"{self.url}\">Переглянути на {self.source}</a> (<code>{self.id}</code>)\n"

        # Description

        if self.description:
            if len(self.description) > _MAX_DESC_LENGTH:
                # Truncate description if it's too long to fit in Telegram message
                text += f"\n<blockquote expandable>{self.description[:_MAX_DESC_LENGTH - 3]}...</blockquote>"

            else:
                # Add full description
                text += f"\n<blockquote expandable>{self.description}</blockquote>"

        return text

    @property
    def brokers_forbidden(self) -> bool:
        """
        Returns True if somewhere in text fields (description, street, building name)
        there are words that indicate that brokers are forbidden
        """

        # Prepare regex phrases
        brokers_re = (
            r"(р[іи][єе]лт[оеа]ра?м?и?ы?"
            r"|посе?редника?м?и?і?в?)"
        )
        please_re = (
            r"(прошу"
            r"|про[сз]ь?ба"
            r"|проханн?я"
            r"|будь[ \-]?ласка"
            r"|п[оа]жалуй?cта"
            r"|пж[лста]*)"
        )
        do_not_re = (
            r"н[еі]т?"
        )
        call_re = (
            r"(турбу(вати|йте)"
            r"|беспоко(ить|йте)"
            r"|цікавлять"
            r"|[иі]нтересують?"
            r"|д?звон[иі]т[ьи]"
            r"|потр[еа]б[уею]т?ь?[ся]"
            r"|потрібн[оі]"
            r"|нужн[оіиы])"
        )
        sep_re = r"[\s,.]*"
        final_re = rf"{brokers_re}{sep_re}{please_re}?{sep_re}{do_not_re}{sep_re}{call_re}"

        for field in (self.street, self.description):
            if re.search(final_re, field, re.IGNORECASE):
                # Found words indicating that brokers are forbidden
                return True

        return False

    def __eq__(self, other: "Advertisement") -> bool:
        """
        Returns true if both advertisements have same ID and source.
        """

        assert isinstance(other, Advertisement), "Can only compare Advertisement instances"
        return self.id == other.id and self.source == other.source


def format_price(value: float | int | None, currency: str) -> str | None:
    """
    Format given price with given currency.
    """

    if value is None:
        # No price
        return None

    return f"${int(value)}" if currency.lower() in ("usd", "$") else f"{int(value)} {currency}"


def save_advertisements(
        advertisements: Advertisement | list[Advertisement],
        *_advertisements: Advertisement,
        update: bool = True,
) -> None:
    """
    Save collected advertisements to a file (for future use).
    If advertisement with given ID and source already exists,
    it will be updated if update=True, otherwise it will be skipped.
    """

    if not isinstance(advertisements, list):
        # Convert to list
        advertisements = [advertisements]

    # Add additional advertisements if provided
    advertisements: list[Advertisement]
    advertisements.extend(_advertisements)

    if not config.advertisements_file.parent.exists():
        # Create parent directory if it doesn't exist
        config.advertisements_file.parent.mkdir(parents=True, exist_ok=True)

    # Check for existing advertisements
    existing: list[Advertisement] = []

    if config.advertisements_file.exists():
        with config.advertisements_file.open("r") as file:
            # Load existing data if file exists
            existing = [Advertisement(**data) for data in load(file)]

    for advertisement in advertisements:
        for index, existing_advertisement in enumerate(existing):
            if advertisement == existing_advertisement:
                # Advertisement with same ID and source already exists
                if update:
                    # Update existing advertisement
                    existing[index] = advertisement

                break
        else:
            # No existing advertisement with same ID and source, add new one
            existing.append(advertisement)

    # Convert to JSON
    data = [advertisement.model_dump() for advertisement in existing]

    with config.advertisements_file.open("w") as file:
        # Save updated data to file
        dump(data, file, default=str, ensure_ascii=False, indent=2)


def load_advertisements() -> list[Advertisement]:
    """
    Load advertisements from file.
    """

    if not config.advertisements_file.exists():
        # No file, return empty list
        return []

    with config.advertisements_file.open("r") as file:
        # Load data from file
        return [Advertisement(**data) for data in load(file)]
