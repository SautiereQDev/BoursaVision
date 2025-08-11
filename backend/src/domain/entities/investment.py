
"""
Investment Entity - Core Business Domain
=========================================

Pure business logic for investment management following DDD principles.
Represents individual investment instruments and their analysis.

Classes:
    InvestmentType: Enumeration of supported investment types
    InvestmentSector: Enumeration of financial sectors
    MarketCap: Enumeration of market capitalization categories
    Investment: Core investment entity with business logic
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from ..events.portfolio_events import InvestmentAnalyzedEvent, InvestmentCreatedEvent
from ..value_objects.money import Currency, Money
from ..value_objects.signal import ConfidenceScore, Signal, SignalAction
from .base import AggregateRoot

@dataclass
class InvestmentCreateParams:
    """Paramètres pour la création d'un investissement."""
    symbol: str
    name: str
    investment_type: 'InvestmentType'
    sector: 'InvestmentSector'
    market_cap: 'MarketCap'
    currency: 'Currency'
    exchange: str
    isin: Optional[str] = None


class InvestmentType(str, Enum):
    """Types of supported investments"""

    STOCK = "STOCK"
    ETF = "ETF"
    BOND = "BOND"
    CRYPTOCURRENCY = "CRYPTOCURRENCY"
    COMMODITY = "COMMODITY"
    REAL_ESTATE = "REAL_ESTATE"


class InvestmentSector(str, Enum):
    """Financial sectors for investments"""

    TECHNOLOGY = "TECHNOLOGY"
    HEALTHCARE = "HEALTHCARE"
    FINANCIAL = "FINANCIAL"
    CONSUMER_DISCRETIONARY = "CONSUMER_DISCRETIONARY"
    CONSUMER_STAPLES = "CONSUMER_STAPLES"
    ENERGY = "ENERGY"
    UTILITIES = "UTILITIES"
    MATERIALS = "MATERIALS"
    INDUSTRIALS = "INDUSTRIALS"
    TELECOMMUNICATIONS = "TELECOMMUNICATIONS"
    REAL_ESTATE = "REAL_ESTATE"


class MarketCap(str, Enum):
    """Market capitalization categories"""

    NANO = "NANO"  # < $50M
    MICRO = "MICRO"  # $50M - $300M
    SMALL = "SMALL"  # $300M - $2B
    MID = "MID"  # $2B - $10B
    LARGE = "LARGE"  # $10B - $200B
    MEGA = "MEGA"  # > $200B


@dataclass  # pylint: disable=too-many-instance-attributes
class FundamentalData:
    """Fundamental analysis data for an investment"""

    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None  # Return on Equity
    revenue_growth: Optional[float] = None
    eps_growth: Optional[float] = None
    dividend_yield: Optional[float] = None
    peg_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def _score_pe_ratio(self) -> tuple[float, float]:
        """Score P/E ratio component"""
        if self.pe_ratio is None or self.pe_ratio <= 0:
            return 0.0, 0.0

        weight = 0.15
        if 10 <= self.pe_ratio <= 25:
            return 20 * weight, weight
        if 5 <= self.pe_ratio < 10 or 25 < self.pe_ratio <= 35:
            return 15 * weight, weight
        return 10 * weight, weight

    def _score_roe(self) -> tuple[float, float]:
        """Score ROE component"""
        if self.roe is None:
            return 0.0, 0.0

        weight = 0.20
        if self.roe >= 15:
            return 20 * weight, weight
        if self.roe >= 10:
            return 15 * weight, weight
        if self.roe >= 5:
            return 10 * weight, weight
        return 0.0, weight

    def _score_revenue_growth(self) -> tuple[float, float]:
        """Score revenue growth component"""
        if self.revenue_growth is None:
            return 0.0, 0.0

        weight = 0.15
        if self.revenue_growth >= 15:
            return 20 * weight, weight
        if self.revenue_growth >= 5:
            return 15 * weight, weight
        if self.revenue_growth >= 0:
            return 10 * weight, weight
        return 0.0, weight

    def _score_debt_to_equity(self) -> tuple[float, float]:
        """Score debt to equity component"""
        if self.debt_to_equity is None:
            return 0.0, 0.0

        weight = 0.10
        if self.debt_to_equity <= 0.3:
            return 15 * weight, weight
        if self.debt_to_equity <= 0.6:
            return 10 * weight, weight
        if self.debt_to_equity <= 1.0:
            return 5 * weight, weight
        return 0.0, weight

    def calculate_fundamental_score(self) -> float:
        """Calculate composite fundamental score (0-100)"""
        # Calculate individual raw scores (0-100) per component
        components = []
        for score, weight in (
            self._score_pe_ratio(),
            self._score_roe(),
            self._score_revenue_growth(),
            self._score_debt_to_equity(),
        ):
            if weight > 0:
                # raw score out of 20 for each component
                raw = (score / weight) if weight else 0.0
                components.append(max(0.0, min(100.0, raw * 5)))  # scale to 0-100
            else:
                components.append(50.0)
        # Return average or neutral if no components
        if components:
            return sum(components) / len(components)
        return 50.0


@dataclass  # pylint: disable=too-many-instance-attributes
class TechnicalData:
    """Technical analysis data for an investment"""

    rsi: Optional[float] = None
    macd_signal: Optional[str] = None  # "BUY", "SELL", "NEUTRAL"
    sma_50: Optional[Money] = None
    sma_200: Optional[Money] = None
    # Position within Bollinger Bands
    bollinger_position: Optional[float] = None
    volume_trend: Optional[str] = None  # "INCREASING", "DECREASING", "STABLE"
    support_level: Optional[Money] = None
    resistance_level: Optional[Money] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def _score_rsi(self) -> tuple[float, float]:
        """Score RSI component"""
        if self.rsi is None:
            return 0.0, 0.0

        weight = 0.25
        if 30 <= self.rsi <= 70:  # Neutral zone
            return 15 * weight, weight
        if 20 <= self.rsi < 30:  # Oversold (potential buy)
            return 20 * weight, weight
        if 70 < self.rsi <= 80:  # Overbought (potential sell)
            return 10 * weight, weight
        # Extreme levels
        return 5 * weight, weight

    def _score_moving_averages(self, current_price: Money) -> tuple[float, float]:
        """Score moving averages trend"""
        if not self.sma_50 or not self.sma_200:
            return 0.0, 0.0

        weight = 0.30
        if self.sma_50.amount > self.sma_200.amount:
            # Bullish trend
            if current_price.amount > self.sma_50.amount:
                return 20.0 * weight, weight
            return 15.0 * weight, weight
        # Bearish trend
        if current_price.amount < self.sma_50.amount:
            return 5.0 * weight, weight
        return 10.0 * weight, weight

    def _score_macd_signal(self) -> tuple[float, float]:
        """Score MACD signal"""
        if not self.macd_signal:
            return 0.0, 0.0

        weight = 0.20
        # Bullish high score, neutral medium, bearish low score
        signal_scores = {
            "BUY": 20.0 * weight,
            "NEUTRAL": 15.0 * weight,
            "SELL": 5.0 * weight,
        }
        return signal_scores.get(self.macd_signal, 10.0 * weight), weight

    def _score_volume_trend(self) -> tuple[float, float]:
        """Score volume trend"""
        if not self.volume_trend:
            return 0.0, 0.0

        weight = 0.15
        volume_scores = {
            "INCREASING": 15 * weight,
            "STABLE": 10 * weight,
            "DECREASING": 5 * weight,
        }
        score = volume_scores.get(self.volume_trend, 10 * weight)
        return score, weight

    def calculate_technical_score(self, current_price: Money) -> float:
        """Calculate composite technical score (0-100)"""
        # Aggregate weighted scores for each component
        components = [
            self._score_rsi(),
            self._score_moving_averages(current_price),
            self._score_macd_signal(),
            self._score_volume_trend(),
        ]
        # Compute raw scores (0-20) for each component
        raws = []
        for score, weight in components:
            if weight > 0:
                raw = score / weight
                raws.append(max(0.0, min(20.0, raw)))
            else:
                raws.append(10.0)  # neutral raw
        # Average raw scores and scale to 0-100
        if raws:
            avg_raw = sum(raws) / len(raws)
            return avg_raw * 5.0
        return 50.0  # Neutral if no data


@dataclass  # pylint: disable=too-many-instance-attributes
class Investment(AggregateRoot):  # pylint: disable=too-many-instance-attributes
    """
    Investment Aggregate Root - Core business entity

    Encapsulates all business logic related to individual investments:
    - Analysis and scoring
    - Signal generation
    - Risk assessment
    - Performance tracking
    """

    id: UUID
    symbol: str
    name: str
    investment_type: InvestmentType
    sector: InvestmentSector
    market_cap: MarketCap
    currency: Currency
    exchange: str
    isin: Optional[str] = None
    current_price: Optional[Money] = None
    fundamental_data: Optional[FundamentalData] = None
    technical_data: Optional[TechnicalData] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_analyzed: Optional[datetime] = None

    def __post_init__(self):
        """Initialize aggregate root functionality"""
        super().__init__()

    @classmethod
    def create(
        cls, *args, **kwargs
    ) -> "Investment":
        """Factory method to create new investment. Compatible avec les tests et l'API interne."""
        # Si appelé avec un seul argument de type InvestmentCreateParams
        if len(args) == 1 and isinstance(args[0], InvestmentCreateParams):
            params = args[0]
            symbol = params.symbol
            name = params.name
            investment_type = params.investment_type
            sector = params.sector
            market_cap = params.market_cap
            currency = params.currency
            exchange = params.exchange
            isin = params.isin
        else:
            symbol = kwargs.get('symbol')
            name = kwargs.get('name')
            investment_type = kwargs.get('investment_type')
            sector = kwargs.get('sector')
            market_cap = kwargs.get('market_cap')
            currency = kwargs.get('currency')
            exchange = kwargs.get('exchange')
            isin = kwargs.get('isin')

        investment_id = uuid4()
        created_at = datetime.now(timezone.utc)

        investment = cls._build_investment(
            investment_id,
            symbol,
            name,
            investment_type,
            sector,
            market_cap,
            currency,
            exchange,
            isin,
            created_at,
        )
        # Emit domain event at creation
        investment._add_domain_event(InvestmentCreatedEvent(
            investment_id, symbol, name, investment_type, sector
        ))
        return investment

    @staticmethod
    def _build_investment(
        investment_id,
        symbol,
        name,
        investment_type,
        sector,
        market_cap,
        currency,
        exchange,
        isin,
        created_at,
    ):
        return Investment(
            id=investment_id,
            symbol=symbol,
            name=name,
            investment_type=investment_type,
            sector=sector,
            market_cap=market_cap,
            currency=currency,
            exchange=exchange,
            isin=isin,
            created_at=created_at,
        )
        # Emit domain event at creation

    def update_price(self, new_price: Money) -> None:
        """Update current price with validation"""
        if new_price.currency != self.currency:
            raise ValueError(
                f"Price currency {new_price.currency} does not match "
                f"investment currency {self.currency}"
            )

        if new_price.amount <= 0:
            raise ValueError("Price must be positive")

        self.current_price = new_price

    def update_fundamental_data(self, fundamental_data: FundamentalData) -> None:
        """Update fundamental analysis data"""
        self.fundamental_data = fundamental_data
        self.last_analyzed = datetime.now(timezone.utc)

    def update_technical_data(self, technical_data: TechnicalData) -> None:
        """Update technical analysis data"""
        self.technical_data = technical_data
        self.last_analyzed = datetime.now(timezone.utc)

    def calculate_composite_score(self) -> float:
        """Calculate composite investment score (0-100)"""
        if not self.current_price:
            return 0.0

        fundamental_score = 50.0  # Default neutral
        technical_score = 50.0  # Default neutral

        if self.fundamental_data:
            fundamental_score = self.fundamental_data.calculate_fundamental_score()

        if self.technical_data:
            technical_score = self.technical_data.calculate_technical_score(
                self.current_price
            )

        # Weighted average: 60% fundamental, 40% technical
        composite_score = (fundamental_score * 0.6) + (technical_score * 0.4)

        return min(100.0, max(0.0, composite_score))

    def _determine_signal_params(
        self, composite_score: float
    ) -> tuple[SignalAction, ConfidenceScore, Money, str]:
        """Determine signal parameters based on composite score"""
        if composite_score >= 75:
            return (
                SignalAction.BUY,
                ConfidenceScore.HIGH,
                Money(
                    self.current_price.amount * Decimal("1.15"),
                    self.current_price.currency,
                ),
                f"Strong analysis (score: {composite_score:.1f})",
            )

        if composite_score >= 60:
            return (
                SignalAction.BUY,
                ConfidenceScore.MEDIUM,
                Money(
                    self.current_price.amount * Decimal("1.08"),
                    self.current_price.currency,
                ),
                f"Good analysis (score: {composite_score:.1f})",
            )

        if composite_score <= 25:
            return (
                SignalAction.SELL,
                ConfidenceScore.HIGH,
                Money(
                    self.current_price.amount * Decimal("0.90"),
                    self.current_price.currency,
                ),
                f"Weak analysis (score: {composite_score:.1f})",
            )

        if composite_score <= 40:
            return (
                SignalAction.SELL,
                ConfidenceScore.MEDIUM,
                Money(
                    self.current_price.amount * Decimal("0.95"),
                    self.current_price.currency,
                ),
                f"Below average analysis (score: {composite_score:.1f})",
            )

        return (
            SignalAction.HOLD,
            ConfidenceScore.MEDIUM,
            self.current_price,
            f"Neutral analysis (score: {composite_score:.1f})",
        )

    def generate_signal(self) -> Signal:
        """Generate investment signal based on analysis"""
        if not self.current_price:
            return Signal(
                symbol=self.symbol,
                action=SignalAction.HOLD,
                confidence_score=ConfidenceScore.LOW,
                generated_at=datetime.now(timezone.utc),
                price_target=None,
                reasoning="No price data available",
            )

        composite_score = self.calculate_composite_score()
        signal_params = self._determine_signal_params(composite_score)
        action, confidence, target_price, reasoning = signal_params

        signal = Signal(
            symbol=self.symbol,
            action=action,
            confidence_score=confidence,
            generated_at=datetime.now(timezone.utc),
            price_target=target_price,
            reasoning=reasoning,
        )

        # Domain event
        self._add_domain_event(
            InvestmentAnalyzedEvent(
                investment_id=self.id,
                symbol=self.symbol,
                composite_score=composite_score,
                signal=signal,
                occurred_at=datetime.now(timezone.utc),
            )
        )

        return signal

    def _assess_market_cap_risk(self) -> bool:
        """Assess market cap risk"""
        return self.market_cap in [MarketCap.NANO, MarketCap.MICRO]

    def _assess_sector_risk(self) -> bool:
        """Assess sector risk"""
        high_risk_sectors = [
            InvestmentSector.TECHNOLOGY,
            InvestmentSector.ENERGY,
            InvestmentSector.TELECOMMUNICATIONS,
        ]
        return self.sector in high_risk_sectors

    def _assess_fundamental_risk(self) -> int:
        """Assess fundamental risk factors"""
        risk_count = 0
        if not self.fundamental_data:
            return risk_count

        if (
            self.fundamental_data.debt_to_equity
            and self.fundamental_data.debt_to_equity > 1.0
        ):
            risk_count += 1

        if self.fundamental_data.pe_ratio and self.fundamental_data.pe_ratio > 50:
            risk_count += 1

        return risk_count

    def _assess_technical_risk(self) -> bool:
        """Assess technical risk"""
        if not self.technical_data or not self.technical_data.rsi:
            return False

        return self.technical_data.rsi > 80 or self.technical_data.rsi < 20

    def assess_risk_level(self) -> str:
        """Assess investment risk level"""
        risk_factors = 0

        if self._assess_market_cap_risk():
            risk_factors += 1

        if self._assess_sector_risk():
            risk_factors += 1

        risk_factors += self._assess_fundamental_risk()

        if self._assess_technical_risk():
            risk_factors += 1

        # Determine overall risk level
        if risk_factors >= 3:
            return "HIGH"
        if risk_factors >= 1:
            return "MEDIUM"
        return "LOW"

    def is_analysis_stale(self, max_age_hours: int = 24) -> bool:
        """Check if analysis data is stale"""
        if not self.last_analyzed:
            return True

        age = datetime.now(timezone.utc) - self.last_analyzed
        return age.total_seconds() > (max_age_hours * 3600)


# Business Exceptions
class InvestmentValidationException(Exception):
    """Raised when investment validation fails"""


class AnalysisDataMissingException(Exception):
    """Raised when required analysis data is missing"""
