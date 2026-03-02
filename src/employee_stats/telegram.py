from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Union

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.config import config
from src.employee_stats.access import Role, resolve
from src.employee_stats.menu import MenuAction, main_menu
from src.employee_stats.presenter import (
    build_all_counts,
    build_all_links_messages,
    build_my_counts,
    build_my_links,
)

bot = Bot(
    token=config.telegram.token,
    default=DefaultBotProperties(
        parse_mode="HTML",
        link_preview_is_disabled=True,
    ),
)

dp = Dispatcher()
router = Router()


def _no_access() -> str:
    """Return a standard access-denied message."""
    return "⛔ Немає доступу"


async def _send_menu(message: Message, role: Role) -> None:
    """
    Send the main menu keyboard based on the user's role.
    """

    await message.answer("Меню:", reply_markup=main_menu(role))


async def _with_progress(
        message: Message,
        coro: Awaitable[Union[str, list[str]]],
        role: Role,
) -> None:
    """
    Run an async action with a small progress indicator.

    Behavior:
      1) Sends "typing" action and a short "collecting data" message.
      2) Replaces that message with the first result chunk (if possible).
      3) Sends remaining chunks as separate messages.

    Notes:
      - We avoid editing reply_markup because aiogram typing hints may reject ReplyKeyboardMarkup.
      - We handle TelegramBadRequest to avoid crashes when editing is not possible.
    """

    # Short UX feedback (Telegram shows it for a few seconds)
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    progress_msg = await message.answer(
        "Збираю інформацію. Будь ласка, зачекайте…",
        reply_markup=main_menu(role),
    )

    try:
        result = await coro
        chunks = result if isinstance(result, list) else [result]
        first_chunk = chunks[0] if chunks else "Немає даних."

        # Try to replace progress message with the first chunk
        try:
            await progress_msg.edit_text(first_chunk)
        except TelegramBadRequest:
            await message.answer(first_chunk, reply_markup=main_menu(role))

        # Send the rest (e.g. per-employee blocks)
        for chunk in chunks[1:]:
            await message.answer(chunk, reply_markup=main_menu(role))

    except Exception:
        error_text = "Сталася помилка під час збору даних. Спробуйте ще раз."
        try:
            await progress_msg.edit_text(error_text)
        except TelegramBadRequest:
            await message.answer(error_text, reply_markup=main_menu(role))
        raise


@router.message(Command("id"))
async def get_id(message: Message) -> None:
    await message.answer(
        f"{message.from_user.full_name}\n"
        f"ID: <code>{message.from_user.id}</code>"
    )


@router.message(CommandStart())
async def start(message: Message) -> None:
    """
    /start handler.

    Shows the menu only for users present in the access list.
    """

    profile = resolve(message.from_user.id)
    if profile is None:
        await message.answer(_no_access())
        return

    await _send_menu(message, profile.role)


@router.message()
async def on_text(message: Message) -> None:
    """
    Handle menu button presses and unknown messages.

    Access rules:
      - Employees: can only request their own stats.
      - Admins: can request both personal and global stats.
    """

    profile = resolve(message.from_user.id)
    if profile is None:
        await message.answer(_no_access())
        return

    role = profile.role
    phone = profile.phone
    text_in = (message.text or "").strip()

    match text_in:
        case MenuAction.MENU.value:
            await _send_menu(message, role)

        case MenuAction.MY_COUNTS.value:
            await _with_progress(message, build_my_counts(phone), role)

        case MenuAction.MY_LINKS.value:
            await _with_progress(message, build_my_links(phone), role)

        case MenuAction.ALL_COUNTS.value if role == Role.ADMIN:
            await _with_progress(message, build_all_counts(), role)

        case MenuAction.ALL_LINKS.value if role == Role.ADMIN:
            await _with_progress(message, build_all_links_messages(), role)

        case MenuAction.ALL_COUNTS.value | MenuAction.ALL_LINKS.value:
            # Employee pressed admin-only action (shouldn't appear, but just in case)
            await message.answer("⛔ Лише для адмінів", reply_markup=main_menu(role))


async def main() -> None:
    """
    Entry point: register router and start polling.
    """

    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
