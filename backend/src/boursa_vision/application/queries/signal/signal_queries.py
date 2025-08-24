"""
Signal Queries - Complete Schema Support
========================================

Advanced queries for trading signal analysis and market intelligence
leveraging the complete market data and analytics schema.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from boursa_vision.application.common import IQuery


@dataclass(frozen=True)
class GetActiveSignalsQuery(IQuery):
    """
    Query to get currently active trading signals.

    Returns active signals with current status and performance
    using the complete signal tracking schema.
    """

    signal_type: str | None = None  # "buy", "sell", "hold"
    portfolio_id: UUID | None = None
    min_confidence: float = 0.6
    include_expired: bool = False


@dataclass(frozen=True)
class GetSignalPerformanceQuery(IQuery):
    """
    Query to get signal performance analysis.

    Analyzes historical signal performance with success rates
    and return analysis using complete tracking data.
    """

    signal_id: UUID | None = None
    signal_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    include_attribution: bool = True


@dataclass(frozen=True)
class GetMarketSignalsQuery(IQuery):
    """
    Query to get market-wide signals and indicators.

    Returns broad market signals and sentiment indicators
    for overall market analysis and trend identification.
    """

    market: str = "US"  # "US", "EU", "ASIA", "GLOBAL"
    signal_strength_min: float = 0.5
    include_sector_signals: bool = True
    include_technical_indicators: bool = False


@dataclass(frozen=True)
class GetPersonalizedSignalsQuery(IQuery):
    """
    Query to get personalized signals for a user.

    Returns signals tailored to user's portfolio and preferences
    with risk-adjusted recommendations.
    """

    user_id: UUID
    risk_tolerance: str = "medium"  # "low", "medium", "high"
    include_portfolio_context: bool = True
    max_signals: int = 20
