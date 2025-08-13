"""Get user portfolios query module."""

from dataclasses import dataclass
from uuid import UUID

from ...common import IQuery


@dataclass(frozen=True)
class GetUserPortfoliosQuery(IQuery):
    """Query to get all portfolios for a user"""

    user_id: UUID
    include_positions: bool = False
