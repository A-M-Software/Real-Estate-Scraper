from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

DEFAULT_FONT_PATH = Path("src/employee_stats/fonts/Arial.ttf")


def register_font(font_path: Path) -> str:
    """
    Register TTF font in ReportLab and return font name.
    Safe to call multiple times.
    """

    if font_path.stem not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_path.stem, str(font_path)))

    return font_path.stem
