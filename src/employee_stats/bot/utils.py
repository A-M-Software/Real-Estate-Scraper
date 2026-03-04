from collections.abc import Awaitable
from typing import Union

from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ReplyKeyboardMarkup

from src.employee_stats.bot.menu import root_menu
from src.employee_stats.config.access import Role


def no_access_text() -> str:
    """
    Return a standard access-denied message.
    """

    return "⛔ Немає доступу"


async def send_menu(message: Message, role: Role) -> None:
    """
    Send the root menu keyboard.
    """

    await message.answer("Меню:", reply_markup=root_menu(role))


async def with_progress(
        message: Message,
        coro: Awaitable[Union[str, list[str]]],
        *,
        reply_markup: ReplyKeyboardMarkup,
) -> None:
    """
    Run an async action with a small progress indicator.
    Keeps provided reply keyboard after completion.
    """

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    progress_msg = await message.answer(
        "Збираю інформацію. Будь ласка, зачекайте…",
        reply_markup=reply_markup,
    )

    try:
        result = await coro
        chunks = result if isinstance(result, list) else [result]
        first_chunk = chunks[0] if chunks else "Немає даних."

        try:
            # edit_text without reply_markup (ReplyKeyboardMarkup is not supported here)
            await progress_msg.edit_text(first_chunk)
        except TelegramBadRequest:
            await message.answer(first_chunk, reply_markup=reply_markup)
        else:
            # re-attach keyboard via a new message
            await message.answer("Оберіть дію 👇", reply_markup=reply_markup)

        for chunk in chunks[1:]:
            await message.answer(chunk, reply_markup=reply_markup)

    except Exception:
        error_text = "Сталася помилка під час збору даних. Спробуйте ще раз."

        try:
            await progress_msg.edit_text(error_text)
        except TelegramBadRequest:
            await message.answer(error_text, reply_markup=reply_markup)
        else:
            await message.answer("Оберіть дію 👇", reply_markup=reply_markup)

        raise
