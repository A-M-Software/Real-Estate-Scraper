from typing import Any


def format_price_per_sqm(price: Any, currency: str, area: Any) -> str:
    """Return 'N CUR/м²' or empty string if not computable."""
    try:
        p = float(price)
        a = float(area)
        if a <= 0:
            return ""
        per = int(round(p / a))
        return f"{per} {currency}/м²".strip()
    except Exception:
        return ""