"""Find investments query module."""

from dataclasses import dataclass
from typing import List, Optional

from ...common import IQuery


@dataclass(frozen=True)
class FindInvestmentsQuery(IQuery):
    """Query to find investments based on criteria"""

    sectors: Optional[List[str]] = None
    investment_types: Optional[List[str]] = None
    market_caps: Optional[List[str]] = None
    currency: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    search_term: Optional[str] = None
    limit: int = 50
    offset: int = 0
