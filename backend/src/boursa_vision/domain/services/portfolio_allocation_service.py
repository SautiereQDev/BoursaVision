"""
Portfolio Allocation Service
===========================

Domain service for portfolio allocation strategies and rebalancing.
Implements various allocation algorithms following DDD principles.

Classes:
    AllocationStrategy: Enum for different allocation strategies.
    AllocationResult: Value object representing allocation results.
    PortfolioAllocationService: Domain service for portfolio allocation.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from ..entities.portfolio import Portfolio
from ..value_objects.money import Money


class AllocationStrategy(str, Enum):
    """Portfolio allocation strategies"""

    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP_WEIGHT = "market_cap_weight"
    RISK_PARITY = "risk_parity"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    MINIMUM_VARIANCE = "minimum_variance"
    MAXIMUM_DIVERSIFICATION = "maximum_diversification"


@dataclass(frozen=True)
class AllocationResult:
    """Result of portfolio allocation calculation"""

    allocations: dict[str, Decimal]  # symbol -> percentage
    expected_return: Decimal
    expected_risk: Decimal
    sharpe_ratio: Decimal
    rebalance_needed: bool
    rebalance_trades: dict[str, Decimal]  # symbol -> amount to trade


class PortfolioAllocationService:
    """
    Domain service for portfolio allocation and rebalancing.

    Provides various allocation strategies and rebalancing logic
    following modern portfolio theory principles.
    """

    def __init__(self):
        self._min_allocation = Decimal("0.01")  # 1% minimum
        self._max_allocation = Decimal("0.50")  # 50% maximum
        self._rebalance_threshold = Decimal("0.05")  # 5% drift threshold

    def calculate_equal_weight_allocation(self, symbols: list[str]) -> AllocationResult:
        """Calculate equal weight allocation"""
        if not symbols:
            raise ValueError("Symbols list cannot be empty")

        allocation_per_symbol = Decimal("1") / Decimal(len(symbols))
        allocations = dict.fromkeys(symbols, allocation_per_symbol)

        return AllocationResult(
            allocations=allocations,
            expected_return=Decimal("0.08"),  # Default assumption
            expected_risk=Decimal("0.15"),  # Default assumption
            sharpe_ratio=Decimal("0.53"),  # (8% - 2%) / 15%
            rebalance_needed=False,
            rebalance_trades={},
        )

    def calculate_market_cap_allocation(
        self, market_caps: dict[str, Decimal]
    ) -> AllocationResult:
        """Calculate market capitalization weighted allocation"""
        if not market_caps:
            raise ValueError("Market caps dictionary cannot be empty")

        total_market_cap = sum(market_caps.values())
        if total_market_cap <= 0:
            raise ValueError("Total market cap must be positive")

        allocations = {
            symbol: cap / total_market_cap for symbol, cap in market_caps.items()
        }

        # Apply allocation constraints
        allocations = self._apply_allocation_constraints(allocations)

        return AllocationResult(
            allocations=allocations,
            expected_return=Decimal("0.09"),
            expected_risk=Decimal("0.16"),
            sharpe_ratio=Decimal("0.56"),
            rebalance_needed=False,
            rebalance_trades={},
        )

    def calculate_risk_parity_allocation(
        self, risk_contributions: dict[str, Decimal]
    ) -> AllocationResult:
        """Calculate risk parity allocation"""
        if not risk_contributions:
            raise ValueError("Risk contributions dictionary cannot be empty")

        # Inverse volatility weighting (simplified risk parity)
        inverse_risks = {
            symbol: Decimal("1") / risk if risk > 0 else Decimal("0")
            for symbol, risk in risk_contributions.items()
        }

        total_inverse_risk = sum(inverse_risks.values())
        if total_inverse_risk <= 0:
            raise ValueError("Total inverse risk must be positive")

        allocations = {
            symbol: inv_risk / total_inverse_risk
            for symbol, inv_risk in inverse_risks.items()
        }

        allocations = self._apply_allocation_constraints(allocations)

        return AllocationResult(
            allocations=allocations,
            expected_return=Decimal("0.075"),
            expected_risk=Decimal("0.12"),
            sharpe_ratio=Decimal("0.625"),
            rebalance_needed=False,
            rebalance_trades={},
        )

    def calculate_momentum_allocation(
        self, momentum_scores: dict[str, Decimal]
    ) -> AllocationResult:
        """Calculate momentum-based allocation"""
        if not momentum_scores:
            raise ValueError("Momentum scores dictionary cannot be empty")

        # Filter positive momentum only
        positive_momentum = {
            symbol: score for symbol, score in momentum_scores.items() if score > 0
        }

        if not positive_momentum:
            # If no positive momentum, use equal weight
            return self.calculate_equal_weight_allocation(list(momentum_scores.keys()))

        total_momentum = sum(positive_momentum.values())
        allocations = {
            symbol: score / total_momentum
            for symbol, score in positive_momentum.items()
        }

        # Add zero allocations for negative momentum assets
        for symbol in momentum_scores:
            if symbol not in allocations:
                allocations[symbol] = Decimal("0")

        allocations = self._apply_allocation_constraints(allocations)

        return AllocationResult(
            allocations=allocations,
            expected_return=Decimal("0.11"),
            expected_risk=Decimal("0.18"),
            sharpe_ratio=Decimal("0.61"),
            rebalance_needed=False,
            rebalance_trades={},
        )

    def check_rebalancing_needed(
        self,
        portfolio: Portfolio,
        target_allocations: dict[str, Decimal],
        current_prices: dict[str, Money],
    ) -> AllocationResult:
        """Check if portfolio needs rebalancing"""
        current_allocations = self._calculate_current_allocations(
            portfolio, current_prices
        )

        # Calculate allocation drift
        max_drift = Decimal("0")
        rebalance_trades = {}

        for symbol in target_allocations:
            current_alloc = current_allocations.get(symbol, Decimal("0"))
            target_alloc = target_allocations[symbol]
            drift = abs(current_alloc - target_alloc)
            max_drift = max(max_drift, drift)

            if drift > self._rebalance_threshold:
                # Calculate required trade
                total_value = portfolio.calculate_total_value(current_prices)
                target_value = total_value.amount * target_alloc
                current_value = total_value.amount * current_alloc
                trade_amount = target_value - current_value
                rebalance_trades[symbol] = trade_amount

        rebalance_needed = max_drift > self._rebalance_threshold

        return AllocationResult(
            allocations=target_allocations,
            expected_return=Decimal("0.08"),  # Would be calculated from holdings
            expected_risk=Decimal("0.15"),  # Would be calculated from holdings
            sharpe_ratio=Decimal("0.53"),
            rebalance_needed=rebalance_needed,
            rebalance_trades=rebalance_trades,
        )

    def _apply_allocation_constraints(
        self, allocations: dict[str, Decimal]
    ) -> dict[str, Decimal]:
        """Apply minimum and maximum allocation constraints"""
        constrained = {}
        total_adjustment = Decimal("0")

        # First pass: apply constraints and calculate adjustment needed
        for symbol, allocation in allocations.items():
            if allocation < self._min_allocation:
                constrained[symbol] = self._min_allocation
                total_adjustment += self._min_allocation - allocation
            elif allocation > self._max_allocation:
                constrained[symbol] = self._max_allocation
                total_adjustment += allocation - self._max_allocation
            else:
                constrained[symbol] = allocation

        # Second pass: redistribute adjustment proportionally
        if abs(total_adjustment) > Decimal("0.001"):  # Avoid tiny adjustments
            adjustable_symbols = [
                s
                for s in constrained
                if self._min_allocation < constrained[s] < self._max_allocation
            ]

            if adjustable_symbols:
                adjustment_per_symbol = total_adjustment / Decimal(
                    len(adjustable_symbols)
                )
                for symbol in adjustable_symbols:
                    constrained[symbol] = max(
                        self._min_allocation,
                        min(
                            self._max_allocation,
                            constrained[symbol] - adjustment_per_symbol,
                        ),
                    )

        # Normalize to ensure sum equals 1
        total_allocation = sum(constrained.values())
        if total_allocation > 0:
            constrained = {
                symbol: allocation / total_allocation
                for symbol, allocation in constrained.items()
            }

        return constrained

    def _calculate_current_allocations(
        self, portfolio: Portfolio, current_prices: dict[str, Money]
    ) -> dict[str, Decimal]:
        """Calculate current portfolio allocations"""
        total_value = portfolio.calculate_total_value(current_prices)

        if total_value.amount <= 0:
            return {}

        current_allocations = {}
        for position in portfolio.positions:
            if position.symbol in current_prices:
                position_value = position.calculate_market_value(
                    current_prices[position.symbol]
                )
                allocation = position_value.amount / total_value.amount
                current_allocations[position.symbol] = allocation

        return current_allocations
