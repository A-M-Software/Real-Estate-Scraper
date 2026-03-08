from datetime import datetime

from src.config import config
from src.advertisment import Advertisement


def filter_ads(
        advertisements: list[Advertisement],
        *,
        date_from: datetime | None,
        date_to: datetime | None,
) -> list[Advertisement]:
    """
    Filter ads by published_at with independent bounds.
    If published_at is missing -> ad is excluded when filters are enabled.
    """

    results: list[Advertisement] = []

    if not (date_from or date_to):
        # No filters
        return advertisements

    for advertisement in advertisements:
        if advertisement.published_at is None:
            # No publication date => skip
            continue

        elif advertisement.published_at.tzinfo is None:
            # Set configured timezone
            advertisement.published_at = advertisement.published_at.astimezone(config.tz)

        if date_from and advertisement.published_at < date_from:
            # Published before the start date => skip
            continue

        if date_to and advertisement.published_at > date_to:
            # Published after the end date => skip
            continue

        results.append(advertisement)

    return results


def build_period_text(
        advertisements: list[Advertisement],
        *,
        date_from: datetime | None,
        date_to: datetime | None,
) -> str:
    """
    Build header period label.
    If filters provided -> show filters.
    Else -> show min/max published_at found in ads.
    """

    if date_from or date_to:
        p_from = date_from.strftime("%Y-%m-%d") if date_from else "—"
        p_to = date_to.strftime("%Y-%m-%d") if date_to else "—"
        return f"Період: {p_from} — {p_to}"

    dt_list = [advertisement.published_at for advertisement in advertisements]
    dt_list = [dt.astimezone(config.tz) if dt and dt.tzinfo is None else dt for dt in dt_list]  # Set timezone if missing
    dt_list = list(filter(None, dt_list))  # Remove None values

    oldest = min(dt_list) if dt_list else None
    newest = max(dt_list) if dt_list else None

    p_from = oldest.strftime("%Y-%m-%d") if oldest else "—"
    p_to = newest.strftime("%Y-%m-%d") if newest else "—"

    return f"Період у файлі: {p_from} — {p_to}"
