from collections.abc import Awaitable
from typing import Union

from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from src.employee_stats.bot.menu import main_menu
from src.employee_stats.config.access import Role


def no_access_text() -> str:
    """
    Return a standard access-denied message.
    """

    return "⛔ Немає доступу"


async def send_menu(message: Message, role: Role) -> None:
    """
    Send the main menu keyboard based on the user's role.
    """

    await message.answer("Меню:", reply_markup=main_menu(role))


async def with_progress(
        message: Message,
        coro: Awaitable[Union[str, list[str]]],
        role: Role,
) -> None:
    """
    Run an async action with a small progress indicator.
    """

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    progress_msg = await message.answer(
        "Збираю інформацію. Будь ласка, зачекайте…",
        reply_markup=main_menu(role),
    )

    try:
        result = await coro
        chunks = result if isinstance(result, list) else [result]
        first_chunk = chunks[0] if chunks else "Немає даних."

        try:

            await progress_msg.edit_text(first_chunk)

        except TelegramBadRequest:
            await message.answer(first_chunk, reply_markup=main_menu(role))

        for chunk in chunks[1:]:
            await message.answer(chunk, reply_markup=main_menu(role))

    except Exception:
        # Defined error-text
        error_text = "Сталася помилка під час збору даних. Спробуйте ще раз."

        try:

            await progress_msg.edit_text(error_text)

        except TelegramBadRequest:
            await message.answer(error_text, reply_markup=main_menu(role))

        raise
