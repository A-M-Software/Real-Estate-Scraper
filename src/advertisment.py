# coding=utf-8

import re
from datetime import datetime
from dataclasses import dataclass
from locale import setlocale, LC_TIME

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .logger import base_logger as logger


_MAX_DESC_LENGTH = 512  # Maximum length of description in Telegram message (to avoid exceeding Telegram limits)


@dataclass
class Advertisement:
    # Apartment info
    city: str
    street: str
    building_name: str | None
    rooms: int | str
    area: int  # Square meters
    description: str

    # Basic info
    id: int
    url: str
    published_at: datetime
    published_at_date: bool  # True if published_at contains only date information without time
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
            text += f"💰 {_fmt_price(price)} ({_fmt_price(price_per_sqm)} за м²)"

        elif price:
            # Only total price
            text += f"💰 {_fmt_price(price)}"

        elif price_per_sqm:
            # Only price per square meter
            text += f"💰 {_fmt_price(price_per_sqm)} за м²"

        text += "\n"

        # Published at

        if self.published_at:
            try:
                # Set locale to Ukrainian for date formatting
                setlocale(LC_TIME, "uk_UA.UTF-8")

            except (ValueError, Exception):
                # Unable to set locale :(
                logger.warning(f"Unable to set 'uk_UA.UTF-8' locale for date formatting")

            text += f"🕓 Опубліковано: "

            if self.published_at_date:
                # No time information, only date
                text += self.published_at.strftime("%d %B (%A)") + "\n"

            else:
                # Date and time information available
                text += self.published_at.strftime("%d %B (%A), %H:%M") + "\n"

        # Broker forbidden

        if self.brokers_forbidden:
            text += "🚫 Посередникам не турбувати\n"

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
    def url_button_markup(self) -> InlineKeyboardMarkup | None:
        """
        Get URL button markup for Telegram message if URL is available
        """

        if self.url:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=f"Переглянути на {self.source}", url=self.url)
                    ],
                ]
            )

    @property
    def brokers_forbidden(self) -> bool:
        """
        Returns True if somewhere in text fields (description, street, building name)
        there are words that indicate that brokers are forbidden
        """

        # Prepare regex phrases
        brokers_re = (
            r"(р[іи][єе]лт[оеа]ра?м?и?ы?"
            r"|посе?редника?м?и?)"
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
