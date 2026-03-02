import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

# Path to a local, non-versioned access list (keep it out of Git)
EMPLOYEES_FILE = Path(__file__).parent / "employees.json"


class Role(StrEnum):
    """
    User role inside the bot access system.
    """

    ADMIN = "admin"
    EMPLOYEE = "employee"


@dataclass(frozen=True)
class Profile:
    """
    Resolved user profile used by the bot handlers.
    """

    role: Role
    name: str
    phone: str


def _load() -> tuple[set[int], dict[int, dict[str, str]]]:
    """
    Load access data from EMPLOYEES_FILE.

    Returns:
        admins: Set of Telegram user IDs with admin permissions.
        employees: Mapping of Telegram user ID -> {"name": str, "phone": str}.
    """

    # Defined some values
    raw_data = json.loads(EMPLOYEES_FILE.read_text(encoding="utf-8"))
    admin_ids = {int(user_id) for user_id in raw_data.get("admins", [])}
    employees_raw: dict[str, dict[str, str]] = raw_data.get("employees", {})
    employees_by_id = {int(tg_id): data for tg_id, data in employees_raw.items()}

    return admin_ids, employees_by_id


def resolve(tg_user_id: int) -> Profile | None:
    """
    Resolve a Telegram user ID to a Profile.

    Args:
        tg_user_id: Telegram user's numeric ID.

    Returns:
        Profile if the user exists in EMPLOYEES_FILE, otherwise None.
    """

    if not EMPLOYEES_FILE.exists():
        return None

    admin_ids, employees_by_id = _load()

    employee_info = employees_by_id.get(tg_user_id)
    if not employee_info:
        return None

    role = Role.ADMIN if tg_user_id in admin_ids else Role.EMPLOYEE
    return Profile(role=role, name=employee_info["name"], phone=employee_info["phone"])


def phone_to_name() -> dict[str, str]:
    """
    Build a helper mapping: phone -> employee name.

    Useful for "all" reports where adverts are grouped by phone.
    """

    if not EMPLOYEES_FILE.exists():
        return {}

    _admin_ids, employees_by_id = _load()
    return {data["phone"]: data["name"] for data in employees_by_id.values()}
