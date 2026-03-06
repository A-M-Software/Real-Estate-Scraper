from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm

from .fonts import DEFAULT_FONT_PATH, register_font
from .models import Layout
from .text import wrap_text
from .filters import filter_ads, build_period_text
from .draw import draw_header, draw_notes_box, ensure_space

from src.config import config
from src.advertisment import format_price, load_advertisements


def export_advertisements_pdf(
        *,
        out_dir: Path,
        title: str = "Виписка оголошень",
        font_path: Path | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
) -> Path:
    """
    Export advertisements from JSON to PDF.

    - Reads `published_at` for filtering and header period text.
    - date_from/date_to are optional and independent bounds.
    - Output is created inside `out_dir`.
    """

    out_dir.mkdir(parents=True, exist_ok=True)

    advertisements = load_advertisements()
    advertisements = filter_ads(
        advertisements,
        date_from=date_from,
        date_to=date_to,
    )

    period_text = build_period_text(
        advertisements if (date_from or date_to) else advertisements,
        date_from=date_from,
        date_to=date_to,
    )

    ts = datetime.now(tz=config.tz).strftime("%Y-%m-%d_%H-%M")
    out_path = out_dir / f"vypyska_{ts}.pdf"

    chosen_font = font_path if (font_path and font_path.exists()) else DEFAULT_FONT_PATH
    font = register_font(chosen_font)

    c = Canvas(str(out_path), pagesize=A4)
    layout = Layout(*A4)

    generated_at = datetime.now(tz=config.tz).strftime("%Y-%m-%d %H:%M")
    page_no = 1

    y = draw_header(
        c,
        layout,
        font=font,
        title=title,
        period_text=period_text,
        generated_at=generated_at,
        page_number=page_no,
    )

    if not advertisements:
        c.setFont(font, 11)
        c.drawString(layout.left, y, "Немає оголошень за вибраним фільтром.")
        c.save()
        return out_path

    # Typography
    header_size = 12
    body_size = 10

    notes_h = 18 * mm

    for index, advertisement in enumerate(advertisements, start=1):

        if advertisement.price_per_sqm:
            # Calculate total price
            price = round(advertisement.price * advertisement.area) if advertisement.area else None
            price_per_sqm = round(advertisement.price)

        else:
            # Calculate price per square meter
            price = advertisement.price
            price_per_sqm = round(advertisement.price / advertisement.area) if advertisement.area else None

        desc_lines = []

        if advertisement.description:
            desc_lines.extend(wrap_text(advertisement.description, font, body_size, layout.content_w))

        desc_h = (len(desc_lines) * 4.2 * mm) if desc_lines else 0

        # Rough height estimate for pagination
        needed = (
                6 * mm
                + 5 * mm
                + 6 * mm
                + (desc_h + (3 * mm if desc_lines else 0))
                + notes_h
                + 10 * mm
        )

        y, new_page = ensure_space(c, layout, y, needed)
        if new_page:
            page_no += 1
            y = draw_header(
                c,
                layout,
                font=font,
                title=title,
                period_text=period_text,
                generated_at=generated_at,
                page_number=page_no,
            )

        # Separator
        c.setLineWidth(0.8)
        c.line(layout.left, y, layout.page_w - layout.right, y)
        y -= 5 * mm

        # Title line
        c.setFont(font, header_size)
        title_text = f"{index}. ID {advertisement.id or '—'}"

        if advertisement.street:
            title_text += f" — {advertisement.street}"

        c.drawString(layout.left, y, title_text)
        y -= 6 * mm

        # Meta + price
        c.setFont(font, body_size)
        meta_left = " • ".join([x for x in [advertisement.source, advertisement.published_at] if x])
        if meta_left:
            c.drawString(layout.left, y, meta_left)

        meta_right = " ".join([x for x in [format_price(price, advertisement.currency)] if x]).strip()
        if meta_right:
            c.drawRightString(layout.page_w - layout.right, y, meta_right)

        y -= 5 * mm

        # Details
        details: list[str] = []

        if advertisement.rooms:
            details.append(f"Кімнат: {advertisement.rooms}")

        if advertisement.area:
            details.append(f"Площа: {advertisement.area} м²")

        if price_per_sqm:
            details.append(f"Ціна за м²: {format_price(price_per_sqm, advertisement.currency)}/м²")

        if advertisement.floor or advertisement.total_floors:
            details.append(
                f"Поверх: {advertisement.floor or '?'}" + (
                    f"/{advertisement.total_floors}" if advertisement.total_floors else ""
                )
            )

        if details:
            c.drawString(layout.left, y, " • ".join(details))
            y -= 6 * mm
        else:
            y -= 2 * mm

        # Description
        if desc_lines:
            for line in desc_lines:
                c.drawString(layout.left, y, line)
                y -= 4.2 * mm
            y -= 3 * mm

        # Notes
        y = draw_notes_box(
            c,
            x=layout.left,
            y_top=y,
            w=layout.content_w,
            h=notes_h,
            font=font,
        )
        y -= 6 * mm

    c.save()

    return out_path
