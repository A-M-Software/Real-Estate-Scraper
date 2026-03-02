import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.employee_stats.bot.menu import MenuAction, main_menu
from src.employee_stats.bot.utils import (
    no_access_text,
    send_menu,
    with_progress,
)
from src.employee_stats.config.access import Role, resolve
from src.employee_stats.presenter.text import (
    build_all_counts,
    build_all_links_messages,
    build_my_counts, build_my_links,
)

# Defined logger
logger = logging.getLogger(__name__)

# Defined router
router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    """
    Greet the user and show the menu (only if user has access).
    """

    profile = resolve(message.from_user.id)

    if profile is None:
        await message.answer(no_access_text())
        return

    logger.info(
        "START | user_id=%s | name=%s | role=%s",
        message.from_user.id,
        profile.name,
        profile.role,
    )

    role_label = "Адміністратор" if profile.role == Role.ADMIN else "Співробітник"
    greeting_text = (
        f"👋 <b>Вітаю, {profile.name}!</b>\n\n"
        f"🏢 Роль: {role_label}\n"
        f"📱 Телефон: <code>{profile.phone}</code>\n\n"
        f"Оберіть дію з меню нижче 👇"
    )

    await message.answer(greeting_text, reply_markup=main_menu(profile.role))


@router.message()
async def on_text(message: Message) -> None:
    """
    Handle menu button presses.
    """

    profile = resolve(message.from_user.id)

    if profile is None:
        await message.answer(no_access_text())
        return

    role = profile.role
    phone = profile.phone
    text_in = (message.text or "").strip()

    logger.info(
        "ACTION | user_id=%s | name=%s | role=%s | action=%s",
        message.from_user.id,
        profile.name,
        profile.role,
        text_in,
    )

    match text_in:
        case MenuAction.MENU.value:
            await send_menu(message, role)

        case MenuAction.MY_COUNTS.value:
            await with_progress(message, build_my_counts(phone), role)

        case MenuAction.MY_LINKS.value:
            await with_progress(message, build_my_links(phone), role)

        case MenuAction.ALL_COUNTS.value if role == Role.ADMIN:
            await with_progress(message, build_all_counts(), role)

        case MenuAction.ALL_LINKS.value if role == Role.ADMIN:
            await with_progress(message, build_all_links_messages(), role)

        case MenuAction.ALL_COUNTS.value | MenuAction.ALL_LINKS.value:
            await message.answer("⛔ Лише для адмінів", reply_markup=main_menu(role))
