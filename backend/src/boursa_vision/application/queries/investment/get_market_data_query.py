"""Get market data query module."""

from dataclasses import dataclass
from datetime import datetime

from ...common import IQuery


@dataclass(frozen=True)
class GetMarketDataQuery(IQuery):
    """Query to get market data for investments"""

    symbols: list[str]
    start_date: datetime | None = None
    end_date: datetime | None = None
    interval: str = "1d"  # 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
