"""Get signals query module."""

from dataclasses import dataclass
from typing import List, Optional

from ...common import IQuery


@dataclass(frozen=True)
class GetSignalsQuery(IQuery):
    """Query to get trading signals"""

    symbols: Optional[List[str]] = None
    signal_types: Optional[List[str]] = None
    min_confidence: float = 0.0
    limit: int = 50
