"""Get portfolio by ID query module."""

from dataclasses import dataclass
from uuid import UUID

from ...common import IQuery


@dataclass(frozen=True)
class GetPortfolioByIdQuery(IQuery):
    """Query to get a specific portfolio by ID"""

    portfolio_id: UUID
    include_positions: bool = True
    include_performance: bool = False
