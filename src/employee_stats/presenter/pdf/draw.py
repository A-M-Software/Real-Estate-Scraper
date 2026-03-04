from reportlab.pdfgen.canvas import Canvas

from .models import Layout
from reportlab.lib.units import mm


def draw_header(
        c: Canvas,
        layout: Layout,
        *,
        font: str,
        title: str,
        period_text: str,
        generated_at: str,
        page_number: int,
) -> float:
    """
    Draw page header and return content start Y.
    """

    y = layout.page_h - layout.top

    c.setFont(font, 16)
    c.drawString(layout.left, y, title)

    c.setFont(font, 9)
    c.drawRightString(layout.page_w - layout.right, y, f"Сторінка {page_number}")
    y -= 6 * mm

    c.setFont(font, 9)
    c.drawString(layout.left, y, period_text)
    c.drawRightString(layout.page_w - layout.right, y, f"Згенеровано: {generated_at}")
    y -= 5 * mm

    c.setLineWidth(1)
    c.line(layout.left, y, layout.page_w - layout.right, y)
    y -= 6 * mm

    return y


def draw_notes_box(
        c: Canvas,
        *,
        x: float,
        y_top: float,
        w: float,
        h: float,
        font: str,
) -> float:
    """
    Draw notes rectangle and return its bottom Y.
    """

    y_bottom = y_top - h

    c.setLineWidth(0.8)
    c.rect(x, y_bottom, w, h)

    c.setFont(font, 9)
    c.drawString(x + 3 * mm, y_top - 4.5 * mm, "Нотатки:")

    return y_bottom


def ensure_space(c: Canvas, layout: Layout, y: float, need: float) -> tuple[float, bool]:
    """
    Ensure enough vertical space for a block.
    Returns: (new_y, started_new_page).
    """

    if y - need >= layout.bottom:
        return y, False

    c.showPage()

    return layout.page_h - layout.top, True
