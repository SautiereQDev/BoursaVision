"""Get investment by symbol query module."""

from dataclasses import dataclass

from ...common import IQuery


@dataclass(frozen=True)
class GetInvestmentBySymbolQuery(IQuery):
    """Query to get a specific investment by symbol"""

    symbol: str
