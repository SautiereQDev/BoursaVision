"""
Performance Analyzer Domain Service
==================================

Domain service for calculating portfolio and investment performance metrics.
Pure business logic without external dependencies.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List

from ..entities.investment import Investment
from ..entities.portfolio import PerformanceMetrics, Portfolio, Position
from ..value_objects.money import Money


@dataclass(frozen=True)
class PerformanceComparison:
    """Performance comparison against benchmarks"""

    portfolio_return: float
    benchmark_return: float
    alpha: float  # Excess return over benchmark
    tracking_error: float
    information_ratio: float


@dataclass(frozen=True)
class RiskAdjustedMetrics:
    """Risk-adjusted performance metrics"""

    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    treynor_ratio: float
    jensen_alpha: float


class PerformanceAnalyzerService:
    """
    Domain service for performance analysis and calculations

    Calculates various performance metrics, risk-adjusted returns,
    and benchmarking comparisons.
    """

    def calculate_portfolio_performance(
        self,
        portfolio: Portfolio,
        positions: List[Position],
        current_prices: Dict[str, Money],
        historical_prices: Dict[str, List[Money]],
        benchmark_returns: List[float] = None,
        risk_free_rate: float = 0.02,
    ) -> PerformanceMetrics:
        """Calculate comprehensive portfolio performance metrics"""

        # Calculate current portfolio value
        total_value = portfolio.calculate_total_value(current_prices)

        # Calculate returns
        daily_return = self._calculate_daily_return(
            portfolio, positions, current_prices, historical_prices
        )
        monthly_return = self._calculate_monthly_return(
            portfolio, positions, current_prices, historical_prices
        )
        annual_return = self._calculate_annual_return(
            portfolio, positions, current_prices, historical_prices
        )

        # Calculate volatility
        portfolio_returns = self._get_portfolio_returns(positions, historical_prices)
        volatility = self._calculate_volatility(portfolio_returns)

        # Calculate Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio(
            annual_return, volatility, risk_free_rate
        )

        # Calculate maximum drawdown
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)

        # Calculate beta
        beta = self._calculate_beta(portfolio_returns, benchmark_returns)

        return PerformanceMetrics(
            total_value=total_value,
            daily_return=daily_return,
            monthly_return=monthly_return,
            annual_return=annual_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            beta=beta,
            last_updated=datetime.now(timezone.utc),
        )

    def calculate_position_performance(
        self, position: Position, current_price: Money, historical_prices: List[Money]
    ) -> Dict[str, float]:
        """Calculate performance metrics for a single position"""

        # Unrealized P&L
        unrealized_pnl = position.calculate_unrealized_pnl(current_price)
        unrealized_pnl_pct = position.calculate_return_percentage(current_price)

        # Time-weighted returns
        if len(historical_prices) >= 2:
            returns = []
            for i in range(1, len(historical_prices)):
                prev_price = historical_prices[i - 1].amount
                curr_price = historical_prices[i].amount
                if prev_price > 0:
                    ret = float((curr_price - prev_price) / prev_price)
                    returns.append(ret)

            # Calculate metrics
            volatility = self._calculate_volatility(returns)
            total_return = self._calculate_cumulative_return(returns)

            # Annualize if we have enough data
            if len(returns) >= 252:  # At least 1 year of daily data
                annual_return = (1 + total_return) ** (252 / len(returns)) - 1
                annual_volatility = volatility * (252**0.5)
            else:
                annual_return = total_return
                annual_volatility = volatility
        else:
            volatility = 0.0
            total_return = 0.0
            annual_return = 0.0
            annual_volatility = 0.0

        return {
            "unrealized_pnl": float(unrealized_pnl.amount),
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "annual_volatility": annual_volatility,
            "market_value": float(position.calculate_market_value(current_price).amount),
        }

    def calculate_risk_adjusted_metrics(
        self,
        portfolio_returns: List[float],
        benchmark_returns: List[float] = None,
        risk_free_rate: float = 0.02,
    ) -> RiskAdjustedMetrics:
        """Calculate risk-adjusted performance metrics"""

        if not portfolio_returns:
            return RiskAdjustedMetrics(
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                treynor_ratio=0.0,
                jensen_alpha=0.0,
            )

        # Calculate basic metrics
        avg_return = sum(portfolio_returns) / len(portfolio_returns)
        volatility = self._calculate_volatility(portfolio_returns)

        # Sharpe Ratio
        excess_return = avg_return - risk_free_rate / 252  # Daily risk-free rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0.0

        # Sortino Ratio (using downside deviation)
        downside_returns = [r for r in portfolio_returns if r < 0]
        if downside_returns:
            downside_deviation = self._calculate_volatility(downside_returns)
            sortino_ratio = (
                excess_return / downside_deviation if downside_deviation > 0 else 0.0
            )
        else:
            sortino_ratio = float("inf") if excess_return > 0 else 0.0

        # Calmar Ratio (return / max drawdown)
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)
        calmar_ratio = avg_return / max_drawdown if max_drawdown > 0 else 0.0

        # Treynor Ratio
        if benchmark_returns:
            beta = self._calculate_beta(portfolio_returns, benchmark_returns)
            treynor_ratio = excess_return / beta if beta > 0 else 0.0

            # Jensen's Alpha
            benchmark_avg = sum(benchmark_returns) / len(benchmark_returns)
            expected_return = risk_free_rate / 252 + beta * (
                benchmark_avg - risk_free_rate / 252
            )
            jensen_alpha = avg_return - expected_return
        else:
            treynor_ratio = 0.0
            jensen_alpha = 0.0

        return RiskAdjustedMetrics(
            sharpe_ratio=sharpe_ratio * (252**0.5),  # Annualized
            sortino_ratio=sortino_ratio * (252**0.5),  # Annualized
            calmar_ratio=calmar_ratio * 252,  # Annualized
            treynor_ratio=treynor_ratio * 252,  # Annualized
            jensen_alpha=jensen_alpha * 252,  # Annualized
        )

    def compare_with_benchmark(
        self, portfolio_returns: List[float], benchmark_returns: List[float]
    ) -> PerformanceComparison:
        """Compare portfolio performance with benchmark"""

        if not portfolio_returns or not benchmark_returns:
            return PerformanceComparison(
                portfolio_return=0.0,
                benchmark_return=0.0,
                alpha=0.0,
                tracking_error=0.0,
                information_ratio=0.0,
            )

        # Align lengths
        min_length = min(len(portfolio_returns), len(benchmark_returns))
        portfolio_ret = portfolio_returns[-min_length:]
        benchmark_ret = benchmark_returns[-min_length:]

        # Calculate cumulative returns
        portfolio_cumulative = self._calculate_cumulative_return(portfolio_ret)
        benchmark_cumulative = self._calculate_cumulative_return(benchmark_ret)

        # Calculate alpha (excess return)
        alpha = portfolio_cumulative - benchmark_cumulative

        # Calculate tracking error
        excess_returns = [p - b for p, b in zip(portfolio_ret, benchmark_ret)]
        tracking_error = self._calculate_volatility(excess_returns)

        # Information ratio
        avg_excess_return = sum(excess_returns) / len(excess_returns)
        information_ratio = (
            avg_excess_return / tracking_error if tracking_error > 0 else 0.0
        )

        return PerformanceComparison(
            portfolio_return=portfolio_cumulative,
            benchmark_return=benchmark_cumulative,
            alpha=alpha,
            tracking_error=tracking_error * (252**0.5),  # Annualized
            information_ratio=information_ratio * (252**0.5),  # Annualized
        )

    def calculate_attribution_analysis(
        self,
        positions: List[Position],
        investments: Dict[str, Investment],
        current_prices: Dict[str, Money],
        historical_prices: Dict[str, List[Money]],
        benchmark_weights: Dict[str, float] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate performance attribution by asset and sector

        Returns:
            Dict with 'assets' and 'sectors' attribution breakdown
        """

        asset_attribution = {}
        sector_attribution = {}

        total_portfolio_value = Decimal("0")

        # Calculate portfolio value
        for position in positions:
            if position.symbol in current_prices:
                market_value = position.calculate_market_value(
                    current_prices[position.symbol]
                )
                total_portfolio_value += market_value.amount

        # Calculate asset-level attribution
        for position in positions:
            if position.symbol not in current_prices:
                continue

            symbol = position.symbol
            current_price = current_prices[symbol]
            market_value = position.calculate_market_value(current_price)

            # Position weight in portfolio
            weight = (
                float(market_value.amount / total_portfolio_value)
                if total_portfolio_value > 0
                else 0.0
            )

            # Calculate position return
            position_return = position.calculate_return_percentage(current_price) / 100

            # Contribution to portfolio return
            contribution = weight * position_return

            asset_attribution[symbol] = {
                "weight": weight,
                "return": position_return,
                "contribution": contribution,
            }

            # Sector attribution
            if symbol in investments:
                sector = investments[symbol].sector.value
                if sector not in sector_attribution:
                    sector_attribution[sector] = {
                        "weight": 0.0,
                        "return": 0.0,
                        "contribution": 0.0,
                    }

                sector_attribution[sector]["weight"] += weight
                sector_attribution[sector]["contribution"] += contribution

        # Calculate sector average returns
        for sector_data in sector_attribution.values():
            if sector_data["weight"] > 0:
                sector_data["return"] = (
                    sector_data["contribution"] / sector_data["weight"]
                )

        return {"assets": asset_attribution, "sectors": sector_attribution}

    def suggest_rebalancing(
        self,
        portfolio: Portfolio,
        positions: List[Position],
        investments: Dict[str, Investment],
        current_prices: Dict[str, Money],
        target_allocation: Dict[str, float] = None,
        rebalance_threshold: float = 0.05,  # 5% threshold
    ) -> List[Dict[str, any]]:
        """Suggest portfolio rebalancing actions"""

        suggestions = []

        if not target_allocation:
            # Default equal-weight allocation
            target_allocation = {pos.symbol: 1.0 / len(positions) for pos in positions}

        portfolio_value = portfolio.calculate_total_value(current_prices)

        for position in positions:
            symbol = position.symbol
            if symbol not in current_prices or symbol not in target_allocation:
                continue

            # Current weight
            market_value = position.calculate_market_value(current_prices[symbol])
            current_weight = float(market_value.amount / portfolio_value.amount)

            # Target weight
            target_weight = target_allocation[symbol]

            # Check if rebalancing is needed
            weight_diff = abs(current_weight - target_weight)
            if weight_diff > rebalance_threshold:
                # Calculate trade amount
                target_value = portfolio_value.amount * Decimal(str(target_weight))
                trade_amount = target_value - market_value.amount

                action = "BUY" if trade_amount > 0 else "SELL"

                suggestions.append(
                    {
                        "symbol": symbol,
                        "action": action,
                        "current_weight": current_weight,
                        "target_weight": target_weight,
                        "weight_difference": current_weight - target_weight,
                        "trade_amount": float(abs(trade_amount)),
                        "reason": f"Weight deviation of {weight_diff:.2%} exceeds threshold",
                    }
                )

        # Sort by weight difference (largest deviations first)
        suggestions.sort(key=lambda x: abs(x["weight_difference"]), reverse=True)

        return suggestions

    # Private helper methods

    def _calculate_daily_return(
        self,
        portfolio: Portfolio,
        positions: List[Position],
        current_prices: Dict[str, Money],
        historical_prices: Dict[str, List[Money]],
    ) -> float:
        """Calculate daily return for portfolio"""

        # Get yesterday's and today's portfolio values
        today_value = portfolio.calculate_total_value(current_prices)

        # Calculate yesterday's prices (last in historical data)
        yesterday_prices = {}
        for symbol, prices in historical_prices.items():
            if prices and len(prices) > 0:
                yesterday_prices[symbol] = prices[-1]

        if not yesterday_prices:
            return 0.0

        yesterday_value = portfolio.calculate_total_value(yesterday_prices)

        if yesterday_value.amount == 0:
            return 0.0

        return float(
            (today_value.amount - yesterday_value.amount) / yesterday_value.amount
        )

    def _calculate_monthly_return(
        self,
        portfolio: Portfolio,
        positions: List[Position],
        current_prices: Dict[str, Money],
        historical_prices: Dict[str, List[Money]],
    ) -> float:
        """Calculate monthly return for portfolio"""

        # Get 30 days ago prices (if available)
        days_ago_prices = {}
        for symbol, prices in historical_prices.items():
            if prices and len(prices) >= 30:
                days_ago_prices[symbol] = prices[-30]

        if not days_ago_prices:
            return 0.0

        current_value = portfolio.calculate_total_value(current_prices)
        past_value = portfolio.calculate_total_value(days_ago_prices)

        if past_value.amount == 0:
            return 0.0

        return float((current_value.amount - past_value.amount) / past_value.amount)

    def _calculate_annual_return(
        self,
        portfolio: Portfolio,
        positions: List[Position],
        current_prices: Dict[str, Money],
        historical_prices: Dict[str, List[Money]],
    ) -> float:
        """Calculate annualized return for portfolio"""

        # Get 252 days ago prices (if available)
        year_ago_prices = {}
        for symbol, prices in historical_prices.items():
            if prices and len(prices) >= 252:
                year_ago_prices[symbol] = prices[-252]

        if not year_ago_prices:
            return 0.0

        current_value = portfolio.calculate_total_value(current_prices)
        past_value = portfolio.calculate_total_value(year_ago_prices)

        if past_value.amount == 0:
            return 0.0

        return float((current_value.amount - past_value.amount) / past_value.amount)

    def _get_portfolio_returns(
        self, positions: List[Position], historical_prices: Dict[str, List[Money]]
    ) -> List[float]:
        """Calculate time series of portfolio returns"""

        # Simplified implementation - equal weights
        all_returns = []

        for symbol, prices in historical_prices.items():
            if len(prices) < 2:
                continue

            symbol_returns = []
            for i in range(1, len(prices)):
                prev_price = prices[i - 1].amount
                curr_price = prices[i].amount
                if prev_price > 0:
                    ret = float((curr_price - prev_price) / prev_price)
                    symbol_returns.append(ret)

            all_returns.append(symbol_returns)

        if not all_returns:
            return []

        # Calculate portfolio returns as average of asset returns (equal weight)
        min_length = min(len(returns) for returns in all_returns)
        portfolio_returns = []

        for i in range(min_length):
            period_return = sum(returns[i] for returns in all_returns) / len(
                all_returns
            )
            portfolio_returns.append(period_return)

        return portfolio_returns

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate volatility (standard deviation) of returns"""
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)

        return variance**0.5

    def _calculate_sharpe_ratio(
        self, annual_return: float, volatility: float, risk_free_rate: float
    ) -> float:
        """Calculate Sharpe ratio"""
        if volatility == 0:
            return 0.0

        return (annual_return - risk_free_rate) / volatility

    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not returns:
            return 0.0

        cumulative = [1.0]
        for ret in returns:
            cumulative.append(cumulative[-1] * (1 + ret))

        max_drawdown = 0.0
        peak = cumulative[0]

        for value in cumulative:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_beta(
        self, portfolio_returns: List[float], benchmark_returns: List[float]
    ) -> float:
        """Calculate portfolio beta relative to benchmark"""
        if not portfolio_returns or not benchmark_returns:
            return 1.0

        # Align lengths
        min_length = min(len(portfolio_returns), len(benchmark_returns))
        if min_length < 2:
            return 1.0

        portfolio_ret = portfolio_returns[-min_length:]
        benchmark_ret = benchmark_returns[-min_length:]

        # Calculate means
        portfolio_mean = sum(portfolio_ret) / len(portfolio_ret)
        benchmark_mean = sum(benchmark_ret) / len(benchmark_ret)

        # Calculate covariance and variance
        covariance = sum(
            (p - portfolio_mean) * (b - benchmark_mean)
            for p, b in zip(portfolio_ret, benchmark_ret)
        ) / (len(portfolio_ret) - 1)

        benchmark_variance = sum((b - benchmark_mean) ** 2 for b in benchmark_ret) / (
            len(benchmark_ret) - 1
        )

        if benchmark_variance == 0:
            return 1.0

        return covariance / benchmark_variance

    def _calculate_cumulative_return(self, returns: List[float]) -> float:
        """Calculate cumulative return from series of returns"""
        if not returns:
            return 0.0

        cumulative = 1.0
        for ret in returns:
            cumulative *= 1 + ret

        return cumulative - 1.0
