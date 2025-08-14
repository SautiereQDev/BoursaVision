from dataclasses import dataclass
from uuid import UUID

from src.application.common import ICommand


@dataclass(frozen=True)
class AddInvestmentToPortfolioCommand(ICommand):
    """Command to add an investment to a portfolio"""

    portfolio_id: UUID
    investment_id: UUID
    quantity: int
    purchase_price: float
    currency: str
