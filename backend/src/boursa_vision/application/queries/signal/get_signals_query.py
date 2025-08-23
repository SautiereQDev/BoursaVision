"""Get signals query module."""

from dataclasses import dataclass

from ...common import IQuery


@dataclass(frozen=True)
class GetSignalsQuery(IQuery):
    """Query to get trading signals"""

    symbols: list[str] | None = None
    signal_types: list[str] | None = None
    min_confidence: float = 0.0
    limit: int = 50
