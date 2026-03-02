from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Counts:
    """
    Aggregated counts of active adverts by type.
    """

    sale: int
    rent: int

    @property
    def total(self) -> int:
        """
        Total number of adverts (sale + rent).
        """

        return self.sale + self.rent


def calc_counts(adverts: list[dict[str, Any]]) -> Counts:
    """
    Calculate sale/rent counts for a list of adverts.

    Sale is determined by SALE_CATEGORY_ID.
    Everything else is treated as rent.
    """

    sale_count = sum(1 for advert in adverts if advert.get("category_id") == 1758)
    rent_count = len(adverts) - sale_count

    return Counts(sale=sale_count, rent=rent_count)
