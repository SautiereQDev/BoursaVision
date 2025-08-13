"""Get investment by ID query module."""

from dataclasses import dataclass
from uuid import UUID

from ...common import IQuery


@dataclass(frozen=True)
class GetInvestmentByIdQuery(IQuery):
    """Query to get a specific investment by ID"""

    investment_id: UUID
