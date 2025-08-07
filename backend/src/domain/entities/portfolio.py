"""
Portfolio Entity - Core Business Domain
======================================

Pure business logic for portfolio management following DDD principles.
No dependencies on external frameworks or infrastructure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID, uuid4

from ..value_objects.money import Money
from ..value_objects.signal import Signal, SignalAction
from ..events.portfolio_events import PortfolioCreatedEvent, InvestmentAddedEvent
from .base import AggregateRoot


@dataclass
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
            current_price.currency
        )
    
    def calculate_unrealized_pnl(self, current_price: Money) -> Money:
        """Calculate unrealized profit/loss"""
        market_value = self.calculate_market_value(current_price)
        book_value = Money(
            self.average_price.amount * Decimal(self.quantity),
            self.average_price.currency
        )
        return Money(
            market_value.amount - book_value.amount,
            market_value.currency
        )
    
    def calculate_return_percentage(self, current_price: Money) -> float:
        """Calculate return percentage"""
        if self.average_price.amount == 0:
            return 0.0
        return float(
            (current_price.amount - self.average_price.amount) 
            / self.average_price.amount * 100
        )


@dataclass
class RiskLimits:
    """Risk management limits for portfolio"""
    max_position_percentage: float = 10.0  # Max 10% per position
    max_sector_exposure: float = 25.0      # Max 25% per sector
    max_daily_loss: float = 5.0            # Max 5% daily loss
    min_cash_percentage: float = 5.0       # Min 5% cash


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
    _positions: Dict[str, Position] = field(default_factory=dict)
    _risk_limits: RiskLimits = field(default_factory=RiskLimits)
    
    @classmethod
    def create(cls, user_id: UUID, name: str, base_currency: str, 
               initial_cash: Money) -> 'Portfolio':
        """Factory method to create new portfolio"""
        portfolio_id = uuid4()
        portfolio = cls(
            id=portfolio_id,
            user_id=user_id,
            name=name,
            base_currency=base_currency,
            cash_balance=initial_cash,
            created_at=datetime.utcnow(),
            _positions={},
            _risk_limits=RiskLimits()
        )
        
        # Domain event
        portfolio._add_domain_event(PortfolioCreatedEvent(
            portfolio_id=portfolio_id,
            user_id=user_id,
            name=name,
            timestamp=datetime.utcnow()
        ))
        
        return portfolio
    
    def add_investment(self, symbol: str, quantity: int, 
                      price: Money, transaction_date: datetime) -> None:
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
            raise InsufficientFundsException(
                f"Insufficient funds. Required: {total_cost}, Available: {self.cash_balance}"
            )
        
        # Rule: Position limit (10% max)
        portfolio_value = self.calculate_total_value({symbol: price})
        position_percentage = (total_cost.amount / portfolio_value.amount) * 100
        if position_percentage > self._risk_limits.max_position_percentage:
            raise PositionLimitExceededException(
                f"Position would exceed {self._risk_limits.max_position_percentage}% limit"
            )
        
        # Update position
        self._update_position(symbol, quantity, price, transaction_date)
        
        # Update cash balance
        self.cash_balance = Money(
            self.cash_balance.amount - total_cost.amount,
            self.cash_balance.currency
        )
        
        # Domain event
        self._add_domain_event(InvestmentAddedEvent(
            portfolio_id=self.id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            timestamp=transaction_date
        ))
    
    def calculate_total_value(self, current_prices: Dict[str, Money]) -> Money:
        """Calculate total portfolio value including cash and positions"""
        total_value = self.cash_balance.amount
        
        for symbol, position in self._positions.items():
            if symbol in current_prices:
                market_value = position.calculate_market_value(current_prices[symbol])
                total_value += market_value.amount
        
        return Money(total_value, self.base_currency)
    
    def calculate_performance_metrics(self, 
                                    current_prices: Dict[str, Money]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        current_value = self.calculate_total_value(current_prices)
        
        # Simplified metrics - would need historical data for accurate calculation
        return PerformanceMetrics(
            total_value=current_value,
            daily_return=0.0,  # Would calculate from historical data
            monthly_return=0.0,
            annual_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            beta=1.0,
            last_updated=datetime.utcnow()
        )
    
    def generate_rebalancing_signals(self, 
                                   target_allocation: Dict[str, float],
                                   current_prices: Dict[str, Money]) -> List[Signal]:
        """Generate rebalancing signals based on target allocation"""
        signals = []
        current_allocation = self._calculate_current_allocation(current_prices)
        total_value = self.calculate_total_value(current_prices)
        
        for symbol, target_pct in target_allocation.items():
            current_pct = current_allocation.get(symbol, 0.0)
            deviation = target_pct - current_pct
            
            # Rebalancing threshold (avoid micro-adjustments)
            if abs(deviation) > 5.0:  # 5% deviation minimum
                action = SignalAction.BUY if deviation > 0 else SignalAction.SELL
                confidence_score = min(abs(deviation) / 10.0, 1.0)  # Max confidence at 10% deviation
                
                target_value = total_value.amount * Decimal(target_pct / 100)
                current_position = self._positions.get(symbol)
                
                if current_position and symbol in current_prices:
                    current_value = current_position.calculate_market_value(current_prices[symbol])
                    amount_difference = target_value - current_value.amount
                else:
                    amount_difference = target_value
                
                signals.append(Signal(
                    symbol=symbol,
                    action=action,
                    confidence_score=confidence_score,
                    price_target=current_prices.get(symbol),
                    amount=Money(abs(amount_difference), self.base_currency),
                    rationale=f"Rebalancing: current {current_pct:.1f}% vs target {target_pct:.1f}%",
                    generated_at=datetime.utcnow()
                ))
        
        return signals
    
    def _update_position(self, symbol: str, quantity: int, 
                        price: Money, transaction_date: datetime) -> None:
        """Update position after transaction"""
        if symbol in self._positions:
            # Update existing position
            existing = self._positions[symbol]
            total_quantity = existing.quantity + quantity
            total_cost = (existing.average_price.amount * existing.quantity + 
                         price.amount * quantity)
            new_average_price = Money(total_cost / total_quantity, price.currency)
            
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=total_quantity,
                average_price=new_average_price,
                first_purchase_date=existing.first_purchase_date,
                last_update=transaction_date
            )
        else:
            # Create new position
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                first_purchase_date=transaction_date,
                last_update=transaction_date
            )
    
    def _calculate_current_allocation(self, 
                                    current_prices: Dict[str, Money]) -> Dict[str, float]:
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
    def positions(self) -> Dict[str, Position]:
        """Read-only access to positions"""
        return self._positions.copy()


# Business Exceptions
class PortfolioException(Exception):
    """Base portfolio exception"""
    pass


class InsufficientFundsException(PortfolioException):
    """Raised when insufficient funds for operation"""
    pass


class PositionLimitExceededException(PortfolioException):
    """Raised when position would exceed risk limits"""
    pass
