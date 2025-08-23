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
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from ..events.portfolio_events import InvestmentCreatedEvent
from ..value_objects.money import Currency, Money
from .base import AggregateRoot


@dataclass
class InvestmentCreateParams:
    """Paramètres pour la création d'un investissement."""

    symbol: str
    name: str
    investment_type: "InvestmentType"
    sector: "InvestmentSector"
    market_cap: "MarketCap"
    currency: "Currency"
    exchange: str
    isin: str | None = None


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

    pe_ratio: float | None = None
    pb_ratio: float | None = None
    debt_to_equity: float | None = None
    roe: float | None = None  # Return on Equity
    revenue_growth: float | None = None
    eps_growth: float | None = None
    dividend_yield: float | None = None
    peg_ratio: float | None = None
    current_ratio: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    def calculate_fundamental_score(self, scoring_service) -> float:
        """
        Calculate the fundamental score using a provided scoring service.
        """
        return scoring_service.calculate_score(self)

    def _score_pe_ratio(self) -> tuple[float, float]:
        """Score P/E ratio."""
        if self.pe_ratio is None:
            return 50.0, 0.0  # Neutral score
        return max(0.0, min(100.0, 100 - self.pe_ratio * 2)), 1.0  # Adjusted scaling

    def _score_roe(self) -> tuple[float, float]:
        """Score ROE."""
        if self.roe is None:
            return 50.0, 0.0  # Neutral score
        return max(0.0, min(100.0, self.roe * 2)), 1.0  # Adjusted scaling

    def _score_revenue_growth(self) -> tuple[float, float]:
        """Score revenue growth."""
        if self.revenue_growth is None:
            return 50.0, 0.0  # Neutral score
        return max(0.0, min(100.0, self.revenue_growth * 2)), 1.0  # Adjusted scaling

    def _score_debt_to_equity(self) -> tuple[float, float]:
        """Score debt-to-equity ratio."""
        if self.debt_to_equity is None:
            return 50.0, 0.0  # Neutral score
        return (
            max(0.0, min(100.0, 100 - self.debt_to_equity * 20)),
            1.0,
        )  # Adjusted scaling


@dataclass  # pylint: disable=too-many-instance-attributes
class TechnicalData:
    """Technical analysis data for an investment"""

    rsi: float | None = None
    macd_signal: str | None = None  # "BUY", "SELL", "NEUTRAL"
    sma_50: Money | None = None
    sma_200: Money | None = None
    # Position within Bollinger Bands
    bollinger_position: float | None = None
    volume_trend: str | None = None  # "INCREASING", "DECREASING", "STABLE"
    support_level: Money | None = None
    resistance_level: Money | None = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

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
    isin: str | None = None
    current_price: Money | None = None
    fundamental_data: FundamentalData | None = None
    technical_data: TechnicalData | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_analyzed: datetime | None = None

    def __post_init__(self):
        """Initialize aggregate root functionality"""
        super().__init__()

    @classmethod
    def create(cls, *args, **kwargs) -> "Investment":
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
            symbol = kwargs.get("symbol")
            name = kwargs.get("name")
            investment_type = kwargs.get("investment_type")
            sector = kwargs.get("sector")
            market_cap = kwargs.get("market_cap")
            currency = kwargs.get("currency")
            exchange = kwargs.get("exchange")
            isin = kwargs.get("isin")

        # Validations
        if not symbol or symbol.strip() == "":
            raise InvestmentValidationException("Symbol cannot be empty")

        if not name or name.strip() == "":
            raise InvestmentValidationException("Name cannot be empty")

        # Normaliser le symbole en majuscules
        symbol = symbol.strip().upper()

        symbol_len = len(symbol)
        if symbol_len < 3 or symbol_len > 10:
            raise InvestmentValidationException(
                f"Symbol length must be between 3 and 10 characters, got {symbol_len}"
            )

        # Valider le format du symbole (lettres et chiffres uniquement)
        if not symbol.isalnum():
            raise InvestmentValidationException(
                f"Symbol must contain only letters and numbers, got '{symbol}'"
            )

        investment_id = uuid4()
        created_at = datetime.now(UTC)

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
        investment._add_domain_event(
            InvestmentCreatedEvent(investment_id, symbol, name, investment_type, sector)
        )
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
        self.last_analyzed = datetime.now(UTC)

    def update_technical_data(self, technical_data: TechnicalData) -> None:
        """Update technical analysis data"""
        self.technical_data = technical_data
        self.last_analyzed = datetime.now(UTC)

    def calculate_composite_score(self):
        """Calculate a composite score based on fundamental and technical data."""
        if not self.fundamental_data or not self.technical_data:
            return 0.0  # Ensure both data sets are present

        # Further refined scoring logic
        fundamental_score = (
            (100 - self.fundamental_data.pe_ratio) * 0.1
            + self.fundamental_data.roe * 0.6
            + self.fundamental_data.revenue_growth * 0.3
            - self.fundamental_data.debt_to_equity * 0.05
        )

        technical_score = (
            (100 - abs(self.technical_data.rsi - 50)) * 0.2
            + (25 if self.technical_data.macd_signal == "BUY" else 0)
            + (20 if self.technical_data.volume_trend == "INCREASING" else -5)
        )

        composite_score = (fundamental_score + technical_score) / 2
        return max(0.0, min(100.0, composite_score))  # Clamp score between 0 and 100

    def generate_signal(self):
        """Generate a signal based on the investment's data."""
        from boursa_vision.domain.value_objects.signal import SignalAction as VOAction

        if not self.fundamental_data or not self.technical_data:
            return VOAction.HOLD  # Default to HOLD if data is missing

        # Adjusted signal generation logic
        if (
            self.fundamental_data.pe_ratio < 25
            and self.fundamental_data.roe > 20
            and self.technical_data.rsi < 65
            and self.technical_data.macd_signal == "BUY"
        ):
            return VOAction.BUY
        if self.fundamental_data.pe_ratio > 40 or self.technical_data.rsi > 75:
            return VOAction.SELL
        return VOAction.HOLD

    def assess_risk_level(self):
        """Assess the risk level of the investment."""
        if not self.fundamental_data or not self.technical_data:
            return "HIGH"  # Default to high risk if data is missing

        # Relaxed risk assessment logic
        debt_to_equity = self.fundamental_data.debt_to_equity
        pe_ratio = self.fundamental_data.pe_ratio
        rsi = self.technical_data.rsi

        if debt_to_equity > 1.5 or pe_ratio > 40 or rsi > 80:
            return "HIGH"
        if 0.5 < debt_to_equity <= 1.5 or 25 < pe_ratio <= 40 or 60 <= rsi <= 80:
            return "MEDIUM"
        return "LOW"

    def is_analysis_stale(self, max_age_hours: int = 24) -> bool:
        """Check if analysis data is stale"""
        if not self.last_analyzed:
            return True

        age = datetime.now(UTC) - self.last_analyzed
        return age.total_seconds() > (max_age_hours * 3600)


# Business Exceptions
class InvestmentValidationException(Exception):
    """Raised when investment validation fails"""


class AnalysisDataMissingException(Exception):
    """Raised when required analysis data is missing"""


class SignalAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
