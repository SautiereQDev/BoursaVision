"""
Portfolio Entity - Core Business Domain
======================================

Pure business logic for portfolio management following DDD principles.
No dependencies on external frameworks or infrastructure.

Classes:
    Position: Represents a position in an asset with methods
    for market value and PnL calculations.
    Portfolio: Represents a portfolio of financial assets,
    managing positions and events.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from ..events import (
    DomainEvent,  # Ensure DomainEvent is imported
    InvestmentAddedEvent,
    PortfolioCreatedEvent,
)
from ..value_objects import (
    ConfidenceScore,
    Currency,
    Money,
    Price,
    Signal,
    SignalAction,
)
from .base import AggregateRoot


@dataclass
# pylint: disable=too-many-instance-attributes
class Position:
    """Value object representing a position in an asset"""

    symbol: str
    quantity: int
    average_price: Money
    first_purchase_date: datetime
    last_update: datetime

    def calculate_market_value(self, current_price: Money) -> Money:
        """Calculate current market value"""
        return Money(
            current_price.amount * Decimal(self.quantity),
            current_price.currency,
        )

    def calculate_unrealized_pnl(self, current_price: Money) -> Money:
        """Calculate unrealized profit/loss"""
        market_value = self.calculate_market_value(current_price)
        book_value = Money(
            self.average_price.amount * Decimal(self.quantity),
            self.average_price.currency,
        )
        return Money(market_value.amount - book_value.amount, market_value.currency)

    def calculate_return_percentage(self, current_price: Money) -> float:
        """Calculate return percentage"""
        if self.average_price.amount == 0:
            return 0.0
        return float(
            (current_price.amount - self.average_price.amount)
            / self.average_price.amount
            * 100
        )


@dataclass
class RiskLimits:
    """Risk management limits for portfolio"""

    max_position_percentage: float = 10.0  # Max 10% per position
    max_sector_exposure: float = 25.0  # Max 25% per sector
    max_daily_loss: float = 5.0  # Max 5% daily loss
    min_cash_percentage: float = 5.0  # Min 5% cash


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics"""

    total_value: Money
    daily_return: float
    monthly_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    last_updated: datetime


@dataclass
# pylint: disable=too-many-instance-attributes
class Portfolio(AggregateRoot):
    """
    Portfolio Aggregate Root - Core business entity

    Encapsulates all business logic related to portfolio management:
    - Investment operations
    - Risk management
    - Performance calculation
    - Rebalancing signals
    """

    id: UUID
    user_id: UUID
    name: str
    base_currency: str
    cash_balance: Money
    created_at: datetime
    _positions: dict[str, Position] = field(default_factory=dict)
    _risk_limits: RiskLimits = field(default_factory=RiskLimits)
    _domain_events: list[DomainEvent] = field(
        default_factory=list
    )  # Fix for missing attribute

    def __post_init__(self):
        """Initialize aggregate root functionality"""
        # Don't call super().__init__() since _domain_events is already a field
        # No operation needed

    @classmethod
    def create(
        cls, user_id: UUID, name: str, base_currency: str, initial_cash: Money
    ) -> "Portfolio":
        """Factory method to create new portfolio"""
        portfolio_id = uuid4()
        created_at = datetime.now(UTC)
        portfolio = cls(
            id=portfolio_id,
            user_id=user_id,
            name=name,
            base_currency=base_currency,
            cash_balance=initial_cash,
            created_at=created_at,
            _positions={},
            _risk_limits=RiskLimits(),
            _domain_events=[],  # Ensure domain events list is initialized
        )

        # Domain event
        portfolio.add_domain_event(
            PortfolioCreatedEvent(portfolio_id, user_id, name, created_at)
        )
        return portfolio

    def add_investment(
        self,
        symbol: str,
        quantity: int,
        price: Money,
        transaction_date: datetime,
    ) -> None:
        """
        Add investment with business rule validation

        Business Rules:
        - Sufficient cash balance
        - Position limit (max 10% per asset)
        - Risk management compliance
        """
        # Rule: Sufficient funds
        total_cost = Money(price.amount * Decimal(quantity), price.currency)
        if total_cost > self.cash_balance:
            raise InsufficientFundsError(
                f"Insufficient funds. Required: {total_cost}, "
                f"Available: {self.cash_balance}"
            )

        # Rule: Position limit (10% max)
        portfolio_value = self.calculate_total_value({symbol: price})
        position_percentage = (total_cost.amount / portfolio_value.amount) * 100
        if position_percentage > self._risk_limits.max_position_percentage:
            raise PositionLimitExceededError(
                f"Position would exceed "
                f"{self._risk_limits.max_position_percentage}% limit"
            )

        # Update position
        self._update_position(symbol, quantity, price, transaction_date)

        # Update cash balance
        self.cash_balance = Money(
            self.cash_balance.amount - total_cost.amount,
            self.cash_balance.currency,
        )

        # Domain event
        self._add_domain_event(
            InvestmentAddedEvent(
                timestamp=transaction_date,
                portfolio_id=self.id,
                symbol=symbol,
                quantity=quantity,
                price=price,
            )
        )

    def calculate_total_value(self, current_prices: dict[str, Money]) -> Money:
        """Calculate total portfolio value including cash and positions"""
        total_value = self.cash_balance.amount

        for symbol, position in self._positions.items():
            if symbol in current_prices:
                market_value = position.calculate_market_value(current_prices[symbol])
                total_value += market_value.amount

        return Money(total_value, Currency(self.base_currency))

    def calculate_performance_metrics(
        self, current_prices: dict[str, Money]
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        current_value = self.calculate_total_value(current_prices)

        # Simplified metrics - would need historical data for
        # accurate calculation
        return PerformanceMetrics(
            total_value=current_value,
            daily_return=0.0,  # Would calculate from historical data
            monthly_return=0.0,
            annual_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            beta=1.0,
            last_updated=datetime.now(UTC),
        )

    def generate_rebalancing_signals(
        self,
        target_allocation: dict[str, float],
        current_prices: dict[str, Money],
    ) -> list[Signal]:
        """Generate rebalancing signals based on target allocation"""
        signals = []
        current_allocation = self._calculate_current_allocation(current_prices)

        for symbol, target_pct in target_allocation.items():
            current_pct = current_allocation.get(symbol, 0.0)
            deviation = target_pct - current_pct

            # Rebalancing threshold (avoid micro-adjustments)
            if abs(deviation) > 5.0:  # 5% deviation minimum
                action = SignalAction.BUY if deviation > 0 else SignalAction.SELL
                confidence_score = min(
                    abs(deviation) / 10.0, 1.0
                )  # Max confidence at 10% deviation

                signals.append(
                    Signal(
                        symbol=symbol,
                        action=action,
                        confidence_score=ConfidenceScore(Decimal(confidence_score)),
                        price_target=(
                            Price(
                                current_prices[symbol].amount,
                                current_prices[symbol].currency,
                            )
                            if symbol in current_prices
                            else None
                        ),
                        reasoning=(
                            "Rebalancing: current "
                            f"{current_pct:.1f}% vs target "
                            f"{target_pct:.1f}%"
                        ),
                        generated_at=datetime.now(UTC),
                    )
                )

        return signals

    def _update_position(
        self,
        symbol: str,
        quantity: int,
        price: Money,
        transaction_date: datetime,
    ) -> None:
        """Update position after transaction"""
        if symbol in self._positions:
            # Update existing position
            existing = self._positions[symbol]
            total_quantity = existing.quantity + quantity
            total_cost = (
                existing.average_price.amount * existing.quantity
                + price.amount * quantity
            )
            new_average_price = Money(total_cost / total_quantity, price.currency)

            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=total_quantity,
                average_price=new_average_price,
                first_purchase_date=existing.first_purchase_date,
                last_update=transaction_date,
            )
        else:
            # Create new position
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                first_purchase_date=transaction_date,
                last_update=transaction_date,
            )

    def _calculate_current_allocation(
        self, current_prices: dict[str, Money]
    ) -> dict[str, float]:
        """Calculate current allocation percentages"""
        total_value = self.calculate_total_value(current_prices)
        allocation = {}

        for symbol, position in self._positions.items():
            if symbol in current_prices:
                market_value = position.calculate_market_value(current_prices[symbol])
                allocation[symbol] = float(
                    (market_value.amount / total_value.amount) * 100
                )

        return allocation

    @property
    def positions(self) -> dict[str, Position]:
        """Read-only access to positions"""
        return self._positions.copy()

    def add_domain_event(self, event):
        """Add a domain event to the portfolio."""
        self._add_domain_event(event)


# Business Exceptions
class PortfolioError(Exception):
    """Base portfolio exception"""


class InsufficientFundsError(PortfolioError):
    """Raised when trying to buy investment without sufficient funds"""


class PositionLimitExceededError(PortfolioError):
    """Raised when trying to exceed position limits"""
