from typing import Any

from reportlab.pdfbase import pdfmetrics


def safe_str(value: Any) -> str:
    """Convert value to trimmed string (None -> '')."""
    return "" if value is None else str(value).strip()


def wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    """Wrap text by word boundaries using current font metrics."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []

    for raw in text.split("\n"):
        words = raw.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for w in words[1:]:
            candidate = f"{current} {w}"
            if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = w

        lines.append(current)

    return lines
