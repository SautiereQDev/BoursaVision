from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.common import ICommand


@dataclass(frozen=True)
class UpdatePortfolioCommand(ICommand):
    """Command to update portfolio information"""

    portfolio_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
