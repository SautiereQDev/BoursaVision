from dataclasses import dataclass
from typing import Optional

from src.application.common import ICommand


@dataclass(frozen=True)
class CreateInvestmentCommand(ICommand):
    """Command to create a new investment"""

    symbol: str
    name: str
    investment_type: str
    sector: str
    market_cap: str
    currency: str
    exchange: str
    isin: Optional[str] = None
