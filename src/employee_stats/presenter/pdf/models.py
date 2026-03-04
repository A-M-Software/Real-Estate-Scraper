from dataclasses import dataclass
from reportlab.lib.units import mm


@dataclass(frozen=True)
class Layout:
    """Page layout and margins (in points)."""

    page_w: float
    page_h: float
    left: float = 16 * mm
    right: float = 16 * mm
    top: float = 14 * mm
    bottom: float = 14 * mm

    @property
    def content_w(self) -> float:
        """Return available content width."""
        return self.page_w - self.left - self.right
