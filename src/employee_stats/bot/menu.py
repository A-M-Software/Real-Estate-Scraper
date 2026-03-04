from enum import StrEnum

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from src.employee_stats.config.access import Role


class MenuSection(StrEnum):
    """
    Top-level menu sections.
    """

    OLX = "🏠 Оголошення OLX"
    REPORTS = "📄 Виписки"
    BACK = "⬅️ Назад"


class OlxAction(StrEnum):
    """
    OLX submenu actions.
    """

    MY_COUNTS = "📊 Мої оголошення — кількість"
    MY_LINKS = "🔗 Мої оголошення — список"
    ALL_COUNTS = "📊 Всі співробітники — кількість"
    ALL_LINKS = "🔗 Всі співробітники — список"
    FIRST_SCRAPED = "📥 Перше оголошення з файлу"


class ReportsAction(StrEnum):
    """
    Reports submenu actions.
    """

    ALL = "📄 Всі виписки"
    RANGE = "📆 Виписка за період"
    LAST_7_DAYS = "🗓 Останні 7 днів"


def root_menu(_: Role) -> ReplyKeyboardMarkup:
    """
    Build top-level menu with sections.
    """

    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(text=MenuSection.OLX.value),
            KeyboardButton(text=MenuSection.REPORTS.value),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Оберіть розділ 👇",
    )


def olx_menu(role: Role) -> ReplyKeyboardMarkup:
    """
    Build OLX submenu depending on user role.

    Admin users see both personal and global statistics.
    Employees see only their own statistics.
    """

    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(text=OlxAction.MY_COUNTS.value),
            KeyboardButton(text=OlxAction.MY_LINKS.value),
        ],
    ]

    if role == Role.ADMIN:
        rows.append(
            [
                KeyboardButton(text=OlxAction.ALL_COUNTS.value),
                KeyboardButton(text=OlxAction.ALL_LINKS.value),
            ],
        )

    rows.append([KeyboardButton(text=MenuSection.BACK.value)])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію 👇",
    )


def reports_menu(_: Role) -> ReplyKeyboardMarkup:
    """
    Build Reports submenu.
    """

    rows: list[list[KeyboardButton]] = [
        [KeyboardButton(text=ReportsAction.ALL.value)],
        [KeyboardButton(text=ReportsAction.RANGE.value)],
        [KeyboardButton(text=ReportsAction.LAST_7_DAYS.value)],
        [KeyboardButton(text=MenuSection.BACK.value)],
    ]

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію 👇",
    )
