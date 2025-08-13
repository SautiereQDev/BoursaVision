from dataclasses import dataclass
from uuid import UUID

from src.application.common import ICommand


@dataclass(frozen=True)
class RemoveInvestmentFromPortfolioCommand(ICommand):
    """Command to remove an investment from a portfolio"""

    portfolio_id: UUID
    investment_id: UUID
    quantity: int
    sale_price: float
    currency: str
