import tempfile
from datetime import datetime, time, timedelta
from pathlib import Path

from aiogram import Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

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
    Bot entry point.

    - Validates user access.
    - Resets active menu to ROOT.
    - Shows the root keyboard (sections).
    """

    profile = resolve(message.from_user.id)

    logger.info(
        "/start command received | user=%s | chat_id=%s",
        message.from_user,
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
    Main text handler (non-FSM).

    Handles:
    - global navigation between sections (ROOT / OLX / REPORTS)
    - OLX submenu actions
    - Reports actions that do not require extra user input

    If FSM is active (date input flow), this handler is skipped
    and FSM-specific handlers take over.
    """

    # If user is in date input flow, do not handle here.
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

    # Global navigation (works from any menu)
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

    match current_menu:
        # -------------------------
        # SECTION: OLX
        # -------------------------
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

                case _:
                    await message.answer("Оберіть дію 👇", reply_markup=olx_menu(role))

        # -------------------------
        # SECTION: REPORTS
        # -------------------------
        case ActiveMenu.REPORTS:
            match text_in:
                # Report: ALL ads
                case ReportsAction.ALL.value:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        pdf_path = export_advertisements_pdf(
                            out_dir=Path(tmp_dir),
                        )

                        await message.answer_document(
                            document=FSInputFile(pdf_path),
                            caption="📄 Виписка оголошень",
                            reply_markup=reports_menu(role),
                        )

                # Report: custom date range (FSM)
                case ReportsAction.RANGE.value:
                    await state.clear()
                    await state.set_state(ReportsRangeState.date_from)

                    await message.answer(
                        "Введіть дату <b>ВІД</b> у форматі <code>YYYY-MM-DD</code>\n"
                        "Приклад: <code>2026-02-01</code>\n\n"
                        "Щоб пропустити мінімальну дату — надішліть <code>-</code>\n"
                        "Щоб вийти — натисніть <b>⬅️ Назад</b>",
                        reply_markup=reports_menu(role),
                    )

                # Report: last 7 days
                case ReportsAction.LAST_7_DAYS.value:
                    now = datetime.now(tz=config.tz)
                    range_start = now - timedelta(days=7)
                    range_end = now

                    with tempfile.TemporaryDirectory() as tmp_dir:
                        pdf_path = export_advertisements_pdf(
                            out_dir=Path(tmp_dir),
                            title="Виписка оголошень за останні 7 днів",
                            date_from=range_start,
                            date_to=range_end,
                        )

                        await message.answer_document(
                            document=FSInputFile(pdf_path),
                            caption=(
                                f"🗓 Останні 7 днів "
                                f"({range_start:%Y-%m-%d} — {range_end:%Y-%m-%d})"
                            ),
                            reply_markup=reports_menu(role),
                        )

                case _:
                    await message.answer("Оберіть дію 👇", reply_markup=reports_menu(role))

        # -------------------------
        # FALLBACK: ROOT
        # -------------------------
        case _:
            await message.answer("Оберіть розділ 👇", reply_markup=root_menu(role))


@router.message(ReportsRangeState.date_from)
async def reports_range_date_from(message: Message, state: FSMContext) -> None:
    """
    FSM step 1: collect start date.

    Allowed inputs:
    - YYYY-MM-DD : set lower bound
    - "-"        : no lower bound
    - "⬅️ Назад" : cancel flow and go back to ROOT
    """

    profile = resolve(message.from_user.id)
    if profile is None:
        await message.answer(no_access_text())
        await state.clear()
        return

    role = profile.role
    text_in = (message.text or "").strip()

    # Allow exiting flow via BACK button while FSM is active
    if text_in == MenuSection.BACK.value:
        await state.clear()
        # stay in Reports menu
        ACTIVE_MENU_BY_USER[message.from_user.id] = ActiveMenu.REPORTS
        await message.answer("⬅️ Назад", reply_markup=reports_menu(role))
        return

    if text_in == "-":
        await state.update_data(date_from=None)
    else:
        try:
            parsed_from = datetime.strptime(text_in, "%Y-%m-%d").date()
        except ValueError:
            await message.answer(
                "❌ Невірний формат. Введіть <code>YYYY-MM-DD</code>, <code>-</code> або <b>⬅️ Назад</b>.",
                reply_markup=reports_menu(role),
            )
            return

        await state.update_data(date_from=parsed_from.isoformat())

    await state.set_state(ReportsRangeState.date_to)

    await message.answer(
        "Введіть дату <b>ДО</b> у форматі <code>YYYY-MM-DD</code>\n"
        "Приклад: <code>2026-02-28</code>\n\n"
        "Щоб пропустити максимальну дату — надішліть <code>-</code>\n"
        "Щоб вийти — натисніть <b>⬅️ Назад</b>",
        reply_markup=reports_menu(role),
    )


@router.message(ReportsRangeState.date_to)
async def reports_range_date_to(message: Message, state: FSMContext) -> None:
    """
    FSM step 2: collect end date and generate PDF.

    Allowed inputs:
    - YYYY-MM-DD : set upper bound
    - "-"        : no upper bound
    - "⬅️ Назад" : cancel flow and go back to ROOT
    """

    profile = resolve(message.from_user.id)
    if profile is None:
        await message.answer(no_access_text())
        await state.clear()
        return

    role = profile.role
    text_in = (message.text or "").strip()

    # Allow exiting flow via BACK button while FSM is active
    if text_in == MenuSection.BACK.value:
        await state.clear()
        # stay in Reports menu
        ACTIVE_MENU_BY_USER[message.from_user.id] = ActiveMenu.REPORTS
        await message.answer("⬅️ Назад", reply_markup=reports_menu(role))
        return

    data = await state.get_data()
    date_from_str: str | None = data.get("date_from")

    # Parse end date input
    if text_in == "-":
        date_to_str: str | None = None
    else:
        try:
            parsed_to = datetime.strptime(text_in, "%Y-%m-%d").date()
        except ValueError:
            await message.answer(
                "❌ Невірний формат. Введіть <code>YYYY-MM-DD</code>, <code>-</code> або <b>⬅️ Назад</b>.",
                reply_markup=reports_menu(role),
            )
            return

        date_to_str = parsed_to.isoformat()

    # Convert independent date bounds to datetimes (inclusive)
    dt_from: datetime | None = None
    dt_to: datetime | None = None

    if date_from_str:
        dt_from = datetime.combine(
            datetime.strptime(date_from_str, "%Y-%m-%d").date(),
            time.min,
            tzinfo=config.tz,
        )

    if date_to_str:
        dt_to = datetime.combine(
            datetime.strptime(date_to_str, "%Y-%m-%d").date(),
            time.max,
            tzinfo=config.tz,
        )

    # Validate range only if both bounds exist
    if dt_from and dt_to and dt_to < dt_from:
        await message.answer(
            "❌ Дата ДО не може бути меншою за дату ВІД.",
            reply_markup=reports_menu(role),
        )
        return

    await state.clear()

    # Generate and send PDF (no server-side saving)
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = export_advertisements_pdf(
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
