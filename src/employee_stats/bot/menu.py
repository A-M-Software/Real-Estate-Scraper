from enum import StrEnum

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from src.employee_stats.config.access import Role


class MenuAction(StrEnum):
    """
    Available menu actions for the bot.
    """

    MY_COUNTS = "📊 Мої оголошення — кількість"
    MY_LINKS = "🔗 Мої оголошення — список"
    ALL_COUNTS = "📊 Всі співробітники — кількість"
    ALL_LINKS = "🔗 Всі співробітники — список"
    MENU = "🏠 Головне меню"


def main_menu(role: Role) -> ReplyKeyboardMarkup:
    """
    Build main reply keyboard depending on user role.

    Admin users see both personal and global statistics.
    Employees see only their own statistics.
    """

    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(text=MenuAction.MY_COUNTS.value),
            KeyboardButton(text=MenuAction.MY_LINKS.value),
        ],
    ]

    # Admin-only actions
    if role == Role.ADMIN:
        rows.append(
            [
                KeyboardButton(text=MenuAction.ALL_COUNTS.value),
                KeyboardButton(text=MenuAction.ALL_LINKS.value),
            ],
        )

    rows.append([KeyboardButton(text=MenuAction.MENU.value)])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію зі списку 👇",
    )
