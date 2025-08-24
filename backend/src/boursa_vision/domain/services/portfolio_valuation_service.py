"""
Portfolio Valuation Service
===========================

Service for real-time portfolio valuation using the complete financial schema.
Provides accurate portfolio valuation with market prices and financial calculations.
"""
from decimal import Decimal
from uuid import UUID

from boursa_vision.domain.entities.investment import Investment
from boursa_vision.domain.entities.portfolio import Portfolio
from boursa_vision.domain.repositories import IMarketDataRepository, IPortfolioRepository
from boursa_vision.domain.value_objects import Money


"""
Portfolio Valuation Service
===========================

Service for real-time portfolio valuation using the complete financial schema.
Provides accurate portfolio valuation with market prices and financial calculations.
"""
from decimal import Decimal
from uuid import UUID

from boursa_vision.domain.entities.portfolio import Portfolio
from boursa_vision.domain.repositories import IMarketDataRepository, IPortfolioRepository
from boursa_vision.domain.value_objects import Money


class PortfolioValuationService:
    """
    Service for comprehensive portfolio valuation.

    Calculates portfolio values using live market data and the complete
    financial schema for accurate real-time portfolio valuation.
    """

    def __init__(
        self,
        portfolio_repository: IPortfolioRepository,
        market_data_repository: IMarketDataRepository,
    ):
        self._portfolio_repository = portfolio_repository
        self._market_data_repository = market_data_repository

    async def calculate_portfolio_value(
        self,
        portfolio_id: UUID,
        use_market_prices: bool = True,
        include_cash: bool = True,
    ) -> Money:
        """
        Calculate total portfolio value.

        Args:
            portfolio_id: Portfolio to valuate
            use_market_prices: Use current market prices vs last known
            include_cash: Include cash balance in total value

        Returns:
            Total portfolio value as Money object
        """
        portfolio = await self._portfolio_repository.find_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        total_value = Decimal("0")

        # Add cash balance if requested
        if include_cash:
            total_value += portfolio.cash_balance.amount

        # Calculate positions value using domain method
        if use_market_prices:
            # Get current prices for all positions
            symbols = list(portfolio._positions.keys())
            current_prices = {}
            
            for symbol in symbols:
                market_data = await self._market_data_repository.find_latest_by_symbol(symbol)
                if market_data:
                    current_prices[symbol] = Money(market_data.close_price, portfolio.base_currency)
                else:
                    # Use last known price from position
                    position = portfolio._positions[symbol]
                    current_prices[symbol] = position.average_price

            portfolio_value = portfolio.calculate_total_value(current_prices)
            total_value = portfolio_value.amount
        else:
            # Use cached values or basic calculation
            total_value += portfolio.cash_balance.amount

        return Money(total_value, portfolio.base_currency)

    async def calculate_positions_breakdown(
        self, portfolio_id: UUID, use_market_prices: bool = True
    ) -> dict[str, dict[str, Decimal]]:
        """
        Calculate detailed breakdown of all positions.

        Returns:
            Dictionary with position details and values
        """
        portfolio = await self._portfolio_repository.find_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        breakdown = {}
        total_positions_value = Decimal("0")

        for symbol, position in portfolio._positions.items():
            # Get current price
            if use_market_prices:
                market_data = await self._market_data_repository.find_latest_by_symbol(symbol)
                current_price = market_data.close_price if market_data else position.average_price.amount
            else:
                current_price = position.average_price.amount

            position_value = current_price * Decimal(position.quantity)
            total_positions_value += position_value

            breakdown[symbol] = {
                "quantity": Decimal(position.quantity),
                "market_value": position_value,
                "cost_basis": position.average_price.amount * Decimal(position.quantity),
                "unrealized_pnl": position_value - (position.average_price.amount * Decimal(position.quantity)),
                "weight_percent": Decimal("0"),  # Will be calculated after
            }

        # Calculate position weights
        if total_positions_value > 0:
            for symbol in breakdown:
                breakdown[symbol]["weight_percent"] = (
                    breakdown[symbol]["market_value"] / total_positions_value * 100
                )

        return breakdown

    async def calculate_unrealized_pnl(self, portfolio_id: UUID) -> Decimal:
        """
        Calculate total unrealized P&L for portfolio.

        Returns:
            Total unrealized P&L amount
        """
        breakdown = await self.calculate_positions_breakdown(portfolio_id)

        total_unrealized_pnl = Decimal("0")
        for position_data in breakdown.values():
            total_unrealized_pnl += position_data["unrealized_pnl"]

        return total_unrealized_pnl

    async def update_portfolio_financials(
        self, portfolio_id: UUID, save_to_repository: bool = True
    ) -> Portfolio:
        """
        Update portfolio financial fields with current calculations.

        This method would update the database model fields like
        current_cash, total_value, daily_pnl, etc. through the repository.

        Args:
            portfolio_id: Portfolio to update
            save_to_repository: Whether to persist changes

        Returns:
            Updated portfolio with refreshed financial data
        """
        portfolio = await self._portfolio_repository.find_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        # Note: The actual financial fields (current_cash, total_value, etc.)
        # are in the database model, not the domain entity.
        # This would be handled by the repository implementation.

        if save_to_repository:
            await self._portfolio_repository.save(portfolio)

        return portfolio
