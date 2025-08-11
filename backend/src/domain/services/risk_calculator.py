"""
Risk Calculator Domain Service
=============================

Domain service for calculating various risk metrics and validating risk limits.
Pure business logic without external dependencies.
"""




from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

from ..entities.investment import Investment, InvestmentSector, MarketCap
from ..entities.portfolio import Portfolio, Position, RiskLimits
from ..utils.performance import calculate_max_drawdown
from ..value_objects.money import Money


@dataclass
class PortfolioRiskInput:
    """Input data for portfolio risk calculation."""
    portfolio: Portfolio
    positions: List[Position]
    investments: Dict[str, Investment]
    current_prices: Dict[str, Money]
    historical_returns: Dict[str, List[float]]



@dataclass(frozen=True)  # pylint: disable=too-many-instance-attributes
class RiskMetrics:
    """Risk metrics for a portfolio"""

    value_at_risk_95: Money  # 95% VaR
    value_at_risk_99: Money  # 99% VaR
    expected_shortfall: Money  # Expected loss beyond VaR
    portfolio_beta: float
    portfolio_volatility: float
    maximum_drawdown: float
    concentration_risk: float  # 0-100, higher = more concentrated
    sector_concentration: Dict[str, float]  # sector -> percentage
    largest_position_weight: float


@dataclass(frozen=True)
class RiskValidationResult:
    """Result of risk validation"""

    is_valid: bool
    violations: List[str]
    warnings: List[str]
    risk_score: float


class RiskCalculatorService:
    """
    Domain service for risk calculations and validations

    Implements various risk management algorithms and business rules
    for portfolio risk assessment.
    """

    def calculate_position_risk(
        self, position: Position, investment: Investment, portfolio_value: Money
    ) -> float:
        """Calculate risk score for a single position (0-100)"""
        risk_score = 0.0

        # Position size risk (weight: 40%)
        position_weight = self._calculate_position_weight(position, portfolio_value)
        position_risk = min(100.0, position_weight * 10)  # 10% = 100 risk
        risk_score += position_risk * 0.4

        # Market cap risk (weight: 25%)
        market_cap_risk = self._get_market_cap_risk(investment.market_cap)
        risk_score += market_cap_risk * 0.25

        # Sector risk (weight: 20%)
        sector_risk = self._get_sector_risk(investment.sector)
        risk_score += sector_risk * 0.20

        # Technical risk (weight: 15%)
        technical_risk = self._get_technical_risk(investment)
        risk_score += technical_risk * 0.15

        return min(100.0, risk_score)

    def calculate_portfolio_risk_metrics(
        self,
        data: 'PortfolioRiskInput',
    ) -> RiskMetrics:
        """Calculate comprehensive risk metrics for portfolio"""
        portfolio_value = data.portfolio.calculate_total_value(data.current_prices)

        # Calculate portfolio returns

        # Calculate portfolio returns
        portfolio_returns = self._calculate_portfolio_returns(
            data.positions, data.historical_returns
        )

        # Value at Risk calculations
        var_95 = self._calculate_var(portfolio_returns, 0.95)
        var_99 = self._calculate_var(portfolio_returns, 0.99)
        expected_shortfall = self._calculate_expected_shortfall(portfolio_returns, 0.95)

        # Convert to money amounts
        var_95_money = Money(
            portfolio_value.amount * Decimal(str(abs(var_95))),
            portfolio_value.currency
        )
        var_99_money = Money(
            portfolio_value.amount * Decimal(str(abs(var_99))),
            portfolio_value.currency
        )
        es_money = Money(
            portfolio_value.amount * Decimal(str(abs(expected_shortfall))),
            portfolio_value.currency
        )

        # Other metrics
        portfolio_beta = self._calculate_portfolio_beta(data.positions, data.investments)
        portfolio_volatility = self._calculate_volatility(portfolio_returns)
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)
        concentration_risk = self._calculate_concentration_risk(
            data.positions,
            data.current_prices
        )
        sector_concentration = self._calculate_sector_concentration(
            data.positions,
            data.investments,
            data.current_prices
        )
        largest_position = self._get_largest_position_weight(data.positions, data.current_prices)

        return RiskMetrics(
            value_at_risk_95=var_95_money,
            value_at_risk_99=var_99_money,
            expected_shortfall=es_money,
            portfolio_beta=portfolio_beta,
            portfolio_volatility=portfolio_volatility,
            maximum_drawdown=max_drawdown,
            concentration_risk=concentration_risk,
            sector_concentration=sector_concentration,
            largest_position_weight=largest_position,
        )

    def validate_risk_limits(
        self,
        portfolio: Portfolio,
        positions: List[Position],
        investments: Dict[str, Investment],
        current_prices: Dict[str, Money],
        risk_limits: RiskLimits,
    ) -> RiskValidationResult:
        """Validate portfolio against risk limits"""
        violations = []
        warnings = []
        risk_score = 0.0

        portfolio_value = portfolio.calculate_total_value(current_prices)

        # Check position limits
        for position in positions:
            position_weight = self._calculate_position_weight(position, portfolio_value)

            if position_weight > risk_limits.max_position_percentage:
                violations.append(
                    f"Position {position.symbol} exceeds limit: "
                    f"{position_weight:.1f}% > "
                    f"{risk_limits.max_position_percentage}%"
                )
                risk_score += 20
            elif position_weight > risk_limits.max_position_percentage * 0.8:
                warnings.append(
                    f"Position {position.symbol} near limit: {position_weight:.1f}%"
                )
                risk_score += 10

        # Check sector concentration
        sector_weights = self._calculate_sector_concentration(
            positions, investments, current_prices
        )

        for sector, weight in sector_weights.items():
            if weight > risk_limits.max_sector_exposure:
                violations.append(
                    f"Sector {sector} exceeds limit: "
                    f"{weight:.1f}% > "
                    f"{risk_limits.max_sector_exposure}%"
                )
                risk_score += 15
            elif weight > risk_limits.max_sector_exposure * 0.8:
                warnings.append(
                    f"Sector {sector} near limit: {weight:.1f}%"
                )
                risk_score += 5

        # Check cash minimum
        cash_percentage = portfolio.cash_balance.amount / portfolio_value.amount * 100
        if cash_percentage < risk_limits.min_cash_percentage:
            violations.append(
                f"Cash below minimum: {cash_percentage:.1f}% < "
                f"{risk_limits.min_cash_percentage}%"
            )
            risk_score += 10

        return RiskValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            risk_score=min(100.0, risk_score),
        )

    def suggest_risk_reduction(
        self,
        portfolio: Portfolio,
        positions: List[Position],
        investments: Dict[str, Investment],
        current_prices: Dict[str, Money],
        risk_limits: RiskLimits,
    ) -> List[str]:
        """Suggest actions to reduce portfolio risk"""
        suggestions = []
        portfolio_value = portfolio.calculate_total_value(current_prices)

        suggestions.extend(self._suggest_reduce_oversized_positions(positions, portfolio_value, risk_limits))
        suggestions.extend(self._suggest_reduce_sector_concentration(positions, investments, current_prices, risk_limits))
        suggestions.extend(self._suggest_reduce_high_risk_positions(positions, investments, portfolio_value))

        return suggestions

    def _suggest_reduce_oversized_positions(self, positions, portfolio_value, risk_limits):
        oversized_positions = []
        for position in positions:
            weight = self._calculate_position_weight(position, portfolio_value)
            if weight > risk_limits.max_position_percentage:
                oversized_positions.append((position.symbol, weight))

        suggestions = []
        if oversized_positions:
            oversized_positions.sort(key=lambda x: x[1], reverse=True)
            for symbol, weight in oversized_positions[:3]:  # Top 3
                target_weight = risk_limits.max_position_percentage
                reduce_by = weight - target_weight
                suggestions.append(
                    f"Reduce {symbol} position by {reduce_by:.1f}% "
                    f"(from {weight:.1f}% to {target_weight:.1f}%)"
                )
        return suggestions

    def _suggest_reduce_sector_concentration(self, positions, investments, current_prices, risk_limits):
        sector_weights = self._calculate_sector_concentration(
            positions, investments, current_prices
        )
        suggestions = []
        for sector, weight in sector_weights.items():
            if weight > risk_limits.max_sector_exposure:
                reduce_by = weight - risk_limits.max_sector_exposure
                suggestions.append(
                    f"Reduce {sector} sector exposure by {reduce_by:.1f}%"
                )
        return suggestions

    def _suggest_reduce_high_risk_positions(self, positions, investments, portfolio_value):
        high_risk_positions = []
        for position in positions:
            if position.symbol in investments:
                investment = investments[position.symbol]
                risk_level = investment.assess_risk_level()
                if risk_level == "HIGH":
                    weight = self._calculate_position_weight(position, portfolio_value)
                    high_risk_positions.append((position.symbol, weight))

        suggestions = []
        if high_risk_positions:
            suggestions.append(
                "Consider reducing exposure to high-risk positions: "
                + ", ".join(
                    [
                        f"{symbol} ({weight:.1f}%)"
                        for symbol, weight in high_risk_positions
                    ]
                )
            )
        return suggestions

    # Private helper methods

    def _calculate_position_weight(
        self, position: Position, portfolio_value: Money
    ) -> float:
        """Calculate position weight as percentage of portfolio"""
        if portfolio_value.amount == 0:
            return 0.0

        # Note: This simplified calculation assumes current_price
        # In real implementation, would need current market price
        position_value = position.average_price.amount * Decimal(position.quantity)
        return float(position_value / portfolio_value.amount * 100)

    def _get_market_cap_risk(self, market_cap: MarketCap) -> float:
        """Get risk score based on market cap (0-100)"""
        risk_scores = {
            MarketCap.MEGA: 10,
            MarketCap.LARGE: 20,
            MarketCap.MID: 40,
            MarketCap.SMALL: 60,
            MarketCap.MICRO: 80,
            MarketCap.NANO: 100,
        }
        return risk_scores.get(market_cap, 50)

    def _get_sector_risk(self, sector: InvestmentSector) -> float:
        """Get risk score based on sector (0-100)"""
        # High volatility sectors
        high_risk_sectors = {
            InvestmentSector.TECHNOLOGY: 70,
            InvestmentSector.ENERGY: 80,
            InvestmentSector.TELECOMMUNICATIONS: 60,
        }

        # Medium volatility sectors
        medium_risk_sectors = {
            InvestmentSector.HEALTHCARE: 45,
            InvestmentSector.FINANCIAL: 50,
            InvestmentSector.CONSUMER_DISCRETIONARY: 55,
            InvestmentSector.INDUSTRIALS: 40,
            InvestmentSector.MATERIALS: 60,
        }

        # Low volatility sectors
        low_risk_sectors = {
            InvestmentSector.UTILITIES: 20,
            InvestmentSector.CONSUMER_STAPLES: 25,
            InvestmentSector.REAL_ESTATE: 35,
        }

        if sector in high_risk_sectors:
            return high_risk_sectors[sector]
        if sector in medium_risk_sectors:
            return medium_risk_sectors[sector]
        if sector in low_risk_sectors:
            return low_risk_sectors[sector]

        return 50.0  # Default medium risk

    def _get_technical_risk(self, investment: Investment) -> float:
        """Get technical risk score for investment (0-100)"""
        if not investment.technical_data:
            return 50.0  # Default medium risk

        risk_score = 0.0

        # RSI risk
        if investment.technical_data.rsi is not None:
            rsi = investment.technical_data.rsi
            if rsi > 80 or rsi < 20:  # Extreme levels
                risk_score += 30
            elif rsi > 70 or rsi < 30:  # Overbought/oversold
                risk_score += 15
            else:
                risk_score += 5  # Neutral

        # Volatility risk (simplified - would use actual volatility data)
        if investment.market_cap in [MarketCap.NANO, MarketCap.MICRO]:
            risk_score += 20

        return min(100.0, risk_score)

    def _calculate_portfolio_returns(  # pylint: disable=too-many-arguments,too-many-locals
        self, positions: List[Position], historical_returns: Dict[str, List[float]]
    ) -> List[float]:
        """Calculate historical portfolio returns"""
        # Simplified implementation
        # In real scenario, would calculate weighted returns based on positions
        if not historical_returns:
            return [0.0] * 252  # Default to 252 trading days

        # For now, return average of all position returns
        all_returns = []
        for symbol in historical_returns:
            all_returns.extend(historical_returns[symbol])

        if not all_returns:
            return [0.0] * 252

        # Return last 252 data points or pad with zeros
        if len(all_returns) >= 252:
            portfolio_returns = all_returns[-252:]
        else:
            portfolio_returns = all_returns
        while len(portfolio_returns) < 252:
            portfolio_returns.append(0.0)

        return portfolio_returns

    def _calculate_var(
        self, returns: List[float], confidence: float
    ) -> float:  # pylint: disable=too-many-arguments
        """Calculate Value at Risk at given confidence level"""
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))

        if index >= len(sorted_returns):
            return sorted_returns[-1]

        return sorted_returns[index]

    def _calculate_expected_shortfall(  # pylint: disable=too-many-arguments
        self, returns: List[float], confidence: float
    ) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        var = self._calculate_var(returns, confidence)
        worse_returns = [r for r in returns if r <= var]

        if not worse_returns:
            return var

        return sum(worse_returns) / len(worse_returns)

    def _calculate_portfolio_beta(
        self, positions: List[Position], investments: Dict[str, Investment]
    ) -> float:
        """Calculate portfolio beta (simplified)"""
        # Simplified calculation - in real scenario would use market data
        # Default beta values by sector
        sector_betas = {
            InvestmentSector.TECHNOLOGY: 1.3,
            InvestmentSector.ENERGY: 1.2,
            InvestmentSector.FINANCIAL: 1.1,
            InvestmentSector.HEALTHCARE: 0.9,
            InvestmentSector.UTILITIES: 0.7,
            InvestmentSector.CONSUMER_STAPLES: 0.8,
        }

        weighted_beta = 0.0
        total_weight = 0.0

        for position in positions:
            if position.symbol in investments:
                investment = investments[position.symbol]
                beta = sector_betas.get(investment.sector, 1.0)

                # Calculate position weight (simplified)
                weight = 1.0 / len(positions)  # Equal weight for simplicity
                weighted_beta += beta * weight
                total_weight += weight

        return weighted_beta / total_weight if total_weight > 0 else 1.0

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility"""
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        daily_vol = variance**0.5

        return daily_vol * (252**0.5)  # Annualized (252 trading days)

    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown (delegated to utils)."""
        return calculate_max_drawdown(returns)

    def _calculate_concentration_risk(
        self, positions: List[Position], current_prices: Dict[str, Money]
    ) -> float:
        """Calculate concentration risk using Herfindahl index"""
        if not positions:
            return 0.0

        # Calculate portfolio value
        total_value = Decimal("0")
        position_values = {}

        for position in positions:
            if position.symbol in current_prices:
                price = current_prices[position.symbol]
                value = price.amount * Decimal(position.quantity)
                position_values[position.symbol] = value
                total_value += value

        if total_value == 0:
            return 0.0

        # Calculate Herfindahl index
        herfindahl = sum(
            (value / total_value) ** 2 for value in position_values.values()
        )

        # Convert to 0-100 scale
        # (1/n = perfectly diversified, 1 = concentrated)
        n = len(positions)
        min_herfindahl = Decimal("1") / Decimal(str(n))
        range_herfindahl = Decimal("1") - min_herfindahl
        normalized = (herfindahl - min_herfindahl) / range_herfindahl

        return float(normalized * 100)

    def _calculate_sector_concentration(
        self,
        positions: List[Position],
        investments: Dict[str, Investment],
        current_prices: Dict[str, Money],
    ) -> Dict[str, float]:
        """Calculate sector concentration percentages"""
        sector_values: Dict[str, Decimal] = {}
        total_value = Decimal("0")

        for position in positions:
            in_investments = position.symbol in investments
            in_prices = position.symbol in current_prices
            if in_investments and in_prices:
                investment = investments[position.symbol]
                price = current_prices[position.symbol]
                value = price.amount * Decimal(position.quantity)

                sector = investment.sector.value
                current_sector_value = sector_values.get(sector, Decimal("0"))
                sector_values[sector] = current_sector_value + value
                total_value += value

        if total_value == 0:
            return {}

        return {
            sector: float(value / total_value * 100)
            for sector, value in sector_values.items()
        }

    def _get_largest_position_weight(
        self, positions: List[Position], current_prices: Dict[str, Money]
    ) -> float:
        """Get weight of largest position"""
        if not positions:
            return 0.0

        total_value = Decimal("0")
        position_values = []

        for position in positions:
            if position.symbol in current_prices:
                price = current_prices[position.symbol]
                value = price.amount * Decimal(position.quantity)
                position_values.append(value)
                total_value += value

        if total_value == 0:
            return 0.0

        if position_values:
            largest_value = max(position_values)
        else:
            largest_value = Decimal("0")
        return float(largest_value / total_value * 100)
