from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from boursa_vision.application.common import ICommand


@dataclass(frozen=True)
class CreatePortfolioCommand(ICommand):
    """Command to create a new portfolio"""

    user_id: UUID
    name: str
    description: Optional[str] = None
    initial_cash_amount: float = 0.0
    currency: str = "USD"
