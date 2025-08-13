from dataclasses import dataclass
from uuid import UUID

from src.application.common import ICommand


@dataclass(frozen=True)
class UpdateInvestmentPriceCommand(ICommand):
    """Command to update investment price"""

    investment_id: UUID
    new_price: float
    currency: str
