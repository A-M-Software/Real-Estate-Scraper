from typing import Any


def group_by_phone(adverts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Group adverts by normalized phone number.

    Notes:
        Phone is taken from advert["contact"]["phone"] and normalized by removing spaces.
    """

    # Set default value
    grouped: dict[str, list[dict[str, Any]]] = {}

    for advert in adverts:
        phone_raw = advert["contact"]["phone"]
        phone = "".join(str(phone_raw).split())  # Normalize phone
        grouped.setdefault(phone, []).append(advert)

    return grouped
