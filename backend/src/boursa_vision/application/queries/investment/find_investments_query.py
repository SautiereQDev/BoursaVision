"""Find investments query module."""

from dataclasses import dataclass

from ...common import IQuery


@dataclass(frozen=True)
class FindInvestmentsQuery(IQuery):
    """Query to find investments based on criteria"""

    sectors: list[str] | None = None
    investment_types: list[str] | None = None
    market_caps: list[str] | None = None
    currency: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    search_term: str | None = None
    limit: int = 50
    offset: int = 0
