import tempfile
from datetime import datetime, time, date, timedelta
from pathlib import Path

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from aiogram.dispatcher.event.bases import SkipHandler

from src.config import config
from src.employee_stats.bot.menu import (
    MenuSection,
    OlxAction,
    ReportsAction,
    olx_menu,
    reports_menu,
    root_menu,
)
from src.employee_stats.bot.state import (
    ACTIVE_MENU_BY_USER,
    ActiveMenu,
    ReportsRangeState,
)
from src.employee_stats.bot.utils import no_access_text, with_progress
from src.employee_stats.config.access import Role, resolve
from src.employee_stats.presenter.pdf.export import export_advertisements_pdf
from src.employee_stats.presenter.text import (
    build_all_counts,
    build_all_links_messages,
    build_my_counts,
    build_my_links,
)
from src.logger import bot_logger as logger

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    """
    Entry point for the bot.

    Greets the user and shows the root menu
    if the user has access to the system.
    """

    profile = resolve(message.from_user.id)

    logger.info(
        "/start command received | user_id=%s | chat_id=%s",
        message.from_user.id,
        message.chat.id,
    )

    if profile is None:
        logger.warning("Unauthorized user attempted to access the bot")
        await message.answer(no_access_text())
        return

    ACTIVE_MENU_BY_USER[message.from_user.id] = ActiveMenu.ROOT

    role_label = "Адміністратор" if profile.role == Role.ADMIN else "Співробітник"

    greeting_text = (
        f"👋 <b>Вітаю, {profile.name}!</b>\n\n"
        f"🏢 Роль: {role_label}\n"
        f"📱 Телефон: <code>{profile.phone}</code>\n\n"
        f"Оберіть розділ 👇"
    )

    await message.answer(greeting_text, reply_markup=root_menu(profile.role))


@router.message()
async def on_text(message: Message, state: FSMContext) -> None:
    """
    Handle all text messages from the user.

    Responsible for:
    - menu navigation
    - triggering OLX actions
    - generating PDF reports
    """

    # If FSM is active (user entering dates) —
    # let FSM handlers process the message
    if await state.get_state() is not None:
        raise SkipHandler

    profile = resolve(message.from_user.id)
    if profile is None:
        await message.answer(no_access_text())
        return

    user_id = message.from_user.id
    role = profile.role
    phone = profile.phone
    text_in = (message.text or "").strip()

    current_menu = ACTIVE_MENU_BY_USER.get(user_id, ActiveMenu.ROOT)

    logger.info(
        "ACTION | user_id=%s | name=%s | role=%s | menu=%s | action=%s",
        user_id,
        profile.name,
        role,
        current_menu,
        text_in,
    )

    # GLOBAL NAVIGATION (works from any menu)
    match text_in:

        case MenuSection.OLX.value:
            ACTIVE_MENU_BY_USER[user_id] = ActiveMenu.OLX
            await message.answer("🏠 Оголошення OLX", reply_markup=olx_menu(role))
            await state.clear()
            return

        case MenuSection.REPORTS.value:
            ACTIVE_MENU_BY_USER[user_id] = ActiveMenu.REPORTS
            await message.answer("📄 Виписки", reply_markup=reports_menu(role))
            await state.clear()
            return

        case MenuSection.BACK.value:
            ACTIVE_MENU_BY_USER[user_id] = ActiveMenu.ROOT
            await message.answer("⬅️ Назад", reply_markup=root_menu(role))
            await state.clear()
            return

        case _:
            pass

    # SECTION: OLX
    match current_menu:
        case ActiveMenu.OLX:
            match text_in:
                case OlxAction.MY_COUNTS.value:
                    await with_progress(
                        message,
                        build_my_counts(phone),
                        reply_markup=olx_menu(role),
                    )

                case OlxAction.MY_LINKS.value:
                    await with_progress(
                        message,
                        build_my_links(phone),
                        reply_markup=olx_menu(role),
                    )

                case OlxAction.ALL_COUNTS.value if role == Role.ADMIN:
                    await with_progress(
                        message,
                        build_all_counts(),
                        reply_markup=olx_menu(role),
                    )

                case OlxAction.ALL_LINKS.value if role == Role.ADMIN:
                    await with_progress(
                        message,
                        build_all_links_messages(),
                        reply_markup=olx_menu(role),
                    )

                case OlxAction.ALL_COUNTS.value | OlxAction.ALL_LINKS.value:
                    await message.answer(
                        "⛔ Лише для адмінів",
                        reply_markup=olx_menu(role),
                    )

        # SECTION: REPORTS
        case ActiveMenu.REPORTS:
            match text_in:
                # Generate report for ALL advertisements
                case ReportsAction.ALL.value:

                    with tempfile.TemporaryDirectory() as tmp_dir:

                        pdf_path = export_advertisements_pdf(
                            json_path=config.advertisements_file,
                            out_dir=Path(tmp_dir),
                        )

                        await message.answer_document(
                            document=FSInputFile(pdf_path),
                            caption="📄 Виписка оголошень",
                            reply_markup=reports_menu(role),
                        )

                # Ask user for date range
                case ReportsAction.RANGE.value:

                    await state.clear()
                    await state.set_state(ReportsRangeState.date_from)

                    await message.answer(
                        "Введіть дату <b>ВІД</b> у форматі <code>YYYY-MM-DD</code>\n"
                        "Приклад: <code>2026-02-01</code>\n\n"
                        "Щоб пропустити мінімальну дату — надішліть <code>-</code>",
                        reply_markup=reports_menu(role),
                    )

                # Generate report for last 7 days
                case ReportsAction.LAST_7_DAYS.value:

                    now = datetime.now()
                    range_start = now - timedelta(days=7)
                    range_end = now

                    with tempfile.TemporaryDirectory() as tmp_dir:

                        pdf_path = export_advertisements_pdf(
                            json_path=config.advertisements_file,
                            out_dir=Path(tmp_dir),
                            title="Виписка оголошень за останні 7 днів",
                            date_from=range_start,
                            date_to=range_end,
                        )

                        await message.answer_document(
                            document=FSInputFile(pdf_path),
                            caption=f"🗓 Останні 7 днів ({range_start:%Y-%m-%d} — {range_end:%Y-%m-%d})",
                            reply_markup=reports_menu(role),
                        )

                case _:
                    await message.answer(
                        "Оберіть дію 👇",
                        reply_markup=reports_menu(role),
                    )

        # DEFAULT FALLBACK
        case _:
            await message.answer(
                "Оберіть розділ 👇",
                reply_markup=root_menu(role),
            )


# FSM: DATE FROM
@router.message(ReportsRangeState.date_from)
async def reports_range_date_from(message: Message, state: FSMContext) -> None:
    """
    Capture the start date of the report range.

    '-' means no lower bound.
    """

    profile = resolve(message.from_user.id)
    if profile is None:
        await message.answer(no_access_text())
        await state.clear()
        return

    role = profile.role
    text_in = (message.text or "").strip()

    if text_in == "-":
        await state.update_data(date_from=None)

    else:
        try:
            parsed_date = datetime.strptime(text_in, "%Y-%m-%d").date()
        except ValueError:

            await message.answer(
                "❌ Невірний формат. Введіть <code>YYYY-MM-DD</code> або <code>-</code>.",
                reply_markup=reports_menu(role),
            )
            return

        await state.update_data(date_from=parsed_date.isoformat())

    await state.set_state(ReportsRangeState.date_to)

    await message.answer(
        "Введіть дату <b>ДО</b> у форматі <code>YYYY-MM-DD</code>\n"
        "Приклад: <code>2026-02-28</code>\n\n"
        "Щоб пропустити максимальну дату — надішліть <code>-</code>",
        reply_markup=reports_menu(role),
    )


# FSM: DATE TO
@router.message(ReportsRangeState.date_to)
async def reports_range_date_to(message: Message, state: FSMContext) -> None:
    """
    Capture the end date of the report range
    and generate the PDF report.
    """

    profile = resolve(message.from_user.id)
    if profile is None:
        await message.answer(no_access_text())
        await state.clear()
        return

    role = profile.role
    text_in = (message.text or "").strip()

    data = await state.get_data()
    date_from_str: str | None = data.get("date_from")

    # Parse end date
    if text_in == "-":
        date_to_str: str | None = None

    else:
        try:
            parsed_to_date: date = datetime.strptime(text_in, "%Y-%m-%d").date()
        except ValueError:

            await message.answer(
                "❌ Невірний формат. Введіть <code>YYYY-MM-DD</code> або <code>-</code>.",
                reply_markup=reports_menu(role),
            )
            return

        date_to_str = parsed_to_date.isoformat()

    # Convert to datetime bounds
    dt_from: datetime | None = None
    dt_to: datetime | None = None

    if date_from_str:
        dt_from = datetime.combine(
            datetime.strptime(date_from_str, "%Y-%m-%d").date(),
            time.min,
        )

    if date_to_str:
        dt_to = datetime.combine(
            datetime.strptime(date_to_str, "%Y-%m-%d").date(),
            time.max,
        )

    if dt_from and dt_to and dt_to < dt_from:
        await message.answer(
            "❌ Дата ДО не може бути меншою за дату ВІД.",
            reply_markup=reports_menu(role),
        )
        return

    await state.clear()

    # Generate report
    with tempfile.TemporaryDirectory() as tmp_dir:

        pdf_path = export_advertisements_pdf(
            json_path=config.advertisements_file,
            out_dir=Path(tmp_dir),
            title="Виписка оголошень за період",
            date_from=dt_from,
            date_to=dt_to,
        )

        caption = "📆 Виписка за період"

        if dt_from and dt_to:
            caption += f" {dt_from:%Y-%m-%d} — {dt_to:%Y-%m-%d}"
        elif dt_from:
            caption += f" від {dt_from:%Y-%m-%d}"
        elif dt_to:
            caption += f" до {dt_to:%Y-%m-%d}"

        await message.answer_document(
            document=FSInputFile(pdf_path),
            caption=caption,
            reply_markup=reports_menu(role),
        )
