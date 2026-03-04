import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .text import safe_str


def parse_ads(raw: Any) -> list[dict[str, Any]]:
    """
    Extract list[dict] from supported JSON shapes.
    """

    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]

    if isinstance(raw, dict):
        items = raw.get("items") or raw.get("advertisements") or raw.get("data") or []
        return [x for x in items if isinstance(x, dict)]

    return []


def load_ads(json_path: Path) -> list[dict[str, Any]]:
    """
    Load and parse ads from .json file.
    """

    raw = json.loads(json_path.read_text(encoding="utf-8"))

    return parse_ads(raw)


def parse_published_dt(value: Any) -> datetime | None:
    """
    Parse published_at value into datetime if possible.
    """

    s = safe_str(value)
    if not s:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    return None


def filter_ads(
        ads: list[dict[str, Any]],
        *,
        date_from: datetime | None,
        date_to: datetime | None,
) -> list[dict[str, Any]]:
    """
    Filter ads by published_at with independent bounds.
    If published_at is missing -> ad is excluded when filters are enabled.
    """

    result: list[dict[str, Any]] = []

    if not (date_from or date_to):
        return ads

    for ad in ads:
        dt = parse_published_dt(ad.get("published_at"))
        if dt is None:
            continue
        if date_from and dt < date_from:
            continue
        if date_to and dt > date_to:
            continue
        result.append(ad)

    return result


def build_period_text(
        ads: list[dict[str, Any]],
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

    dt_list = [parse_published_dt(a.get("published_at")) for a in ads]
    dt_list = [x for x in dt_list if x is not None]

    oldest = min(dt_list) if dt_list else None
    newest = max(dt_list) if dt_list else None

    p_from = oldest.strftime("%Y-%m-%d") if oldest else "—"
    p_to = newest.strftime("%Y-%m-%d") if newest else "—"

    return f"Період у файлі: {p_from} — {p_to}"
