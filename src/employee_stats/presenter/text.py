from html import escape
from typing import Any

from src.employee_stats.config.access import phone_to_name
from src.employee_stats.domain.adverts import get_active_cached
from src.employee_stats.domain.grouping import group_by_phone
from src.employee_stats.domain.counters import calc_counts


def _is_sale(advert: dict[str, Any]) -> bool:
    """
    Determine whether an advert is a "sale" advert.

    Sale adverts are identified by SALE_CATEGORY_ID.
    """
    return advert.get("category_id") == 1758


def _split_sale_rent(
        adverts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Split adverts into (sale, rent) buckets.

    Returns:
        sale_adverts, rent_adverts
    """

    # Defined sale and rent adverts
    sale_adverts = [advert for advert in adverts if _is_sale(advert)]
    rent_adverts = [advert for advert in adverts if not _is_sale(advert)]

    return sale_adverts, rent_adverts


def _counts_block(title: str, sale_count: int, rent_count: int) -> str:
    """
    Render a statistics block (total/sale/rent) in Telegram HTML format.
    """

    total_count = sale_count + rent_count

    return (
        f"{title}\n"
        f"📌 <b>Разом</b>: {total_count}\n"
        f"🏷 <b>Продаж</b>: {sale_count}\n"
        f"🏠 <b>Оренда</b>: {rent_count}\n"
    )


def _links_sections(adverts: list[dict[str, Any]], *, limit: int) -> str:
    """
    Render two sections of links: sale and rent.

    Args:
        adverts: List of adverts to render.
        limit: Max items per section to include.
    """

    # Set default value
    parts: list[str] = []

    sale_adverts, rent_adverts = _split_sale_rent(adverts)

    parts.append("🏷 <b>Продаж</b>")
    parts.append(_links_block(sale_adverts, limit=limit))

    parts.append("")  # Visual separator

    parts.append("🏠 <b>Оренда</b>")
    parts.append(_links_block(rent_adverts, limit=limit))

    return "\n".join(parts).strip()


def _title_link(advert: dict[str, Any]) -> str:
    """
    Convert an advert into a clickable HTML link using its title.

    Falls back to "Оголошення" if title is missing.
    """

    title = escape(str(advert.get("title") or "Оголошення"))
    url = escape(str(advert.get("url") or ""))

    return f'<a href="{url}">{title}</a>' if url else title


def _links_block(adverts: list[dict[str, Any]], limit: int) -> str:
    """
    Render a numbered list of advert links (Telegram HTML).

    Args:
        adverts: List of adverts.
        limit: Max number of adverts to include.
    """

    lines = [f"🔗 {idx}. {_title_link(advert)}" for idx, advert in enumerate(adverts[:limit], start=1)]

    return "\n".join(lines) if lines else "📭 Немає оголошень."


async def build_my_counts(phone: str) -> str:
    """
    Build a personal statistics message (counts only) for a given phone number.
    """

    active_adverts = await get_active_cached()
    adverts_by_phone = group_by_phone(active_adverts)
    my_adverts = adverts_by_phone.get(phone, [])

    counts = calc_counts(my_adverts)

    return _counts_block("Мої активні оголошення:", counts.sale, counts.rent).strip()


async def build_my_links(phone: str, *, limit: int = 20) -> str:
    """
    Build a personal message with counts + links grouped by sale/rent.
    """

    active_adverts = await get_active_cached()
    adverts_by_phone = group_by_phone(active_adverts)
    my_adverts = adverts_by_phone.get(phone, [])

    counts = calc_counts(my_adverts)

    text = _counts_block("Мої активні оголошення:", counts.sale, counts.rent)
    text += "\n"
    text += _links_sections(my_adverts, limit=limit)

    return text.strip()


async def build_all_counts() -> str:
    """
    Build an admin message with counts for everyone (no links).
    """

    active_adverts = await get_active_cached()
    adverts_by_phone = group_by_phone(active_adverts)

    total_counts = calc_counts(active_adverts)
    text = _counts_block("📊 <b>Всього активних</b>", total_counts.sale, total_counts.rent) + "\n"

    name_by_phone = phone_to_name()

    for phone, phone_adverts in adverts_by_phone.items():
        counts = calc_counts(phone_adverts)
        title = _fmt_person(name_by_phone.get(phone, phone), phone) if phone in name_by_phone else f"📞 <b>{phone}</b>"
        text += _counts_block(title, counts.sale, counts.rent) + "\n"

    return text.strip()


async def build_all_links_messages(*, limit_per_phone: int = 20) -> list[str]:
    """
    Build admin messages with:
      - first message: overall totals
      - next messages: per-phone blocks with links split into sale/rent

    We return multiple messages to avoid Telegram 4096-char limit.
    """

    active_adverts = await get_active_cached()
    adverts_by_phone = group_by_phone(active_adverts)

    total_counts = calc_counts(active_adverts)
    messages: list[str] = [
        _counts_block("📊 <b>Всього активних</b>", total_counts.sale, total_counts.rent).strip(),
    ]

    name_by_phone = phone_to_name()

    for phone, phone_adverts in adverts_by_phone.items():
        counts = calc_counts(phone_adverts)
        title = _fmt_person(name_by_phone.get(phone, phone), phone) if phone in name_by_phone else f"📞 <b>{phone}</b>"

        text = _counts_block(title, counts.sale, counts.rent)
        text += "\n"
        text += _links_sections(phone_adverts, limit=limit_per_phone)

        messages.append(text.strip())

    return messages


def _fmt_person(name: str, phone: str) -> str:
    """
    Format a person label with masked phone number.

    Example:
        👤 <b>Марина</b> <code>096***97</code>
    """

    normalized_phone = phone[3:] if phone.startswith("+38") else phone
    masked_phone = f"{normalized_phone[:3]}***{normalized_phone[-2:]}"

    return f"👤 <b>{escape(name)}</b> <code>{masked_phone}</code>"
