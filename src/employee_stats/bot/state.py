from enum import StrEnum
from aiogram.fsm.state import State, StatesGroup

ACTIVE_MENU_BY_USER: dict[int, ActiveMenu] = {}


class ActiveMenu(StrEnum):
    ROOT = "ROOT"
    OLX = "OLX"
    REPORTS = "REPORTS"


class ReportsRangeState(StatesGroup):
    date_from = State()
    date_to = State()

