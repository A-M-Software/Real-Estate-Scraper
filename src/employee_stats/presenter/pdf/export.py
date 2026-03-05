from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm

from .fonts import DEFAULT_FONT_PATH, register_font
from .models import Layout
from .text import safe_str, wrap_text
from .money import format_price_per_sqm
from .filters import load_ads, filter_ads, build_period_text
from .draw import draw_header, draw_notes_box, ensure_space

from src.config import config


def export_advertisements_pdf(
        *,
        json_path: Path,
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

    all_ads = load_ads(json_path)
    selected_ads = filter_ads(all_ads, date_from=date_from, date_to=date_to)

    period_text = build_period_text(
        selected_ads if (date_from or date_to) else all_ads,
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

    if not selected_ads:
        c.setFont(font, 11)
        c.drawString(layout.left, y, "Немає оголошень за вибраним фільтром.")
        c.save()
        return out_path

    # Typography
    header_size = 12
    body_size = 10

    notes_h = 18 * mm

    for index, ad in enumerate(selected_ads, start=1):
        ad_id = safe_str(ad.get("id"))
        street = safe_str(ad.get("street"))
        rooms = safe_str(ad.get("rooms"))
        area = ad.get("area")

        description = safe_str(ad.get("description"))
        published_at = safe_str(ad.get("published_at"))
        source = safe_str(ad.get("source"))

        price = ad.get("price")
        currency = safe_str(ad.get("currency"))

        area_str = safe_str(area)
        price_str = safe_str(price)
        per_sqm = format_price_per_sqm(price, currency, area)

        desc_lines = wrap_text(description, font, body_size, layout.content_w) if description else []
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
        title_text = f"{index}. ID {ad_id or '—'}"
        if street:
            title_text += f" — {street}"
        c.drawString(layout.left, y, title_text)
        y -= 6 * mm

        # Meta + price
        c.setFont(font, body_size)
        meta_left = " • ".join([x for x in [source, published_at] if x])
        if meta_left:
            c.drawString(layout.left, y, meta_left)

        meta_right = " ".join([x for x in [price_str, currency] if x]).strip()
        if meta_right:
            c.drawRightString(layout.page_w - layout.right, y, meta_right)

        y -= 5 * mm

        # Details
        details: list[str] = []
        if rooms:
            details.append(f"Кімнат: {rooms}")
        if area_str:
            details.append(f"Площа: {area_str} м²")
        if per_sqm:
            details.append(f"Ціна за м²: {per_sqm}")

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
