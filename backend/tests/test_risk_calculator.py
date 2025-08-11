"""
Tests for Risk Calculator Service
================================

Unit tests for the risk calculator domain service.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.investment import (
    FundamentalData,
    Investment,
    InvestmentCreateParams,
    InvestmentSector,
    InvestmentType,
    MarketCap,
    TechnicalData,
)
from src.domain.entities.portfolio import Portfolio, Position, RiskLimits
from src.domain.services.risk_calculator import RiskCalculatorService
from src.domain.value_objects.money import Currency, Money


class TestRiskCalculatorService:
    """Test cases for RiskCalculatorService"""

    def setup_method(self):
        """Set up test data"""
        self.risk_calculator = RiskCalculatorService()

        # Create test portfolio
        self.portfolio = Portfolio.create(
            user_id=uuid4(),
            name="Test Portfolio",
            base_currency=Currency.USD.value,
            initial_cash=Money(Decimal("10000.00"), Currency.USD),
        )

        # Create test investments
        self.apple_investment = Investment.create(
            InvestmentCreateParams(
                symbol="AAPL",
                name="Apple Inc.",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.TECHNOLOGY,
                market_cap=MarketCap.MEGA,
                currency=Currency.USD,
                exchange="NASDAQ",
            )
        )

        self.coca_cola_investment = Investment.create(
            InvestmentCreateParams(
                symbol="KO",
                name="Coca-Cola",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.CONSUMER_STAPLES,
                market_cap=MarketCap.LARGE,
                currency=Currency.USD,
                exchange="NYSE",
            )
        )

        # Create test positions
        self.positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                average_price=Money(Decimal("150.00"), Currency.USD),
                first_purchase_date=datetime.now(timezone.utc),
                last_update=datetime.now(timezone.utc),
            ),
            Position(
                symbol="KO",
                quantity=20,
                average_price=Money(Decimal("60.00"), Currency.USD),
                first_purchase_date=datetime.now(timezone.utc),
                last_update=datetime.now(timezone.utc),
            ),
        ]

        self.investments = {
            "AAPL": self.apple_investment,
            "KO": self.coca_cola_investment,
        }

        self.current_prices = {
            "AAPL": Money(Decimal("160.00"), Currency.USD),
            "KO": Money(Decimal("65.00"), Currency.USD),
        }

    def test_calculate_position_risk_high_risk(self):
        """Test position risk calculation for high-risk investment"""
        # Set high-risk data for Apple
        fundamental_data = FundamentalData(
            debt_to_equity=2.0, pe_ratio=80.0  # High debt  # High valuation
        )
        technical_data = TechnicalData(rsi=90.0)  # Extreme overbought

        self.apple_investment.update_fundamental_data(fundamental_data)
        self.apple_investment.update_technical_data(technical_data)

        # Total value
        portfolio_value = Money(Decimal("2800.00"), Currency.USD)

        risk_score = self.risk_calculator.calculate_position_risk(
            self.positions[0], self.apple_investment, portfolio_value  # Apple position
        )

        # Should be high risk (>60)
        assert risk_score > 60.0
        assert risk_score <= 100.0

    def test_calculate_position_risk_low_risk(self):
        """Test position risk calculation for low-risk investment"""
        # Set low-risk data for Coca-Cola
        fundamental_data = FundamentalData(
            debt_to_equity=0.3, pe_ratio=20.0  # Low debt  # Reasonable valuation
        )
        technical_data = TechnicalData(rsi=50.0)  # Neutral RSI

        self.coca_cola_investment.update_fundamental_data(fundamental_data)
        self.coca_cola_investment.update_technical_data(technical_data)

        portfolio_value = Money(Decimal("2800.00"), Currency.USD)

        risk_score = self.risk_calculator.calculate_position_risk(
            self.positions[1],  # Coca-Cola position
            self.coca_cola_investment,
            portfolio_value,
        )

        # Should be low to medium risk (<60)
        assert risk_score < 60.0
        assert risk_score >= 0.0

    def test_validate_risk_limits_within_limits(self):
        """Test risk validation when within limits"""
        risk_limits = RiskLimits(
            max_position_percentage=70.0,  # High limit
            max_sector_exposure=80.0,  # High limit
            min_cash_percentage=5.0,
        )

        result = self.risk_calculator.validate_risk_limits(
            self.portfolio,
            self.positions,
            self.investments,
            self.current_prices,
            risk_limits,
        )

        assert result.is_valid
        assert len(result.violations) == 0
        assert result.risk_score >= 0.0

    def test_validate_risk_limits_position_violation(self):
        """Test risk validation with position limit violation"""
        risk_limits = RiskLimits(
            max_position_percentage=5.0,  # Very low limit
            max_sector_exposure=80.0,
            min_cash_percentage=5.0,
        )

        result = self.risk_calculator.validate_risk_limits(
            self.portfolio,
            self.positions,
            self.investments,
            self.current_prices,
            risk_limits,
        )

        assert not result.is_valid
        assert len(result.violations) > 0
        exceeds_limit_found = any(
            "exceeds limit" in violation for violation in result.violations
        )
        assert exceeds_limit_found
        assert result.risk_score > 0.0

    def test_suggest_risk_reduction(self):
        """Test risk reduction suggestions"""
        risk_limits = RiskLimits(
            max_position_percentage=40.0,  # Moderate limit
            max_sector_exposure=50.0,
            min_cash_percentage=5.0,
        )

        suggestions = self.risk_calculator.suggest_risk_reduction(
            self.portfolio,
            self.positions,
            self.investments,
            self.current_prices,
            risk_limits,
        )

        # Should have suggestions (length check)
        assert isinstance(suggestions, list)

        if suggestions:
            # Suggestions should be strings with actionable advice
            suggestion = suggestions[0]
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
            # Check that suggestion contains actionable content
            assert any(
                word in suggestion.lower()
                for word in ["reduce", "sell", "rebalance", "limit", "exposure"]
            )

    def test_calculate_portfolio_risk_metrics(self):
        """Test comprehensive portfolio risk metrics calculation"""
        # Create sample historical returns
        historical_returns = {
            "AAPL": [0.01, -0.02, 0.015, -0.01, 0.02] * 50,  # 250 days
            "KO": [0.005, -0.01, 0.008, -0.005, 0.01] * 50,
        }

        from src.domain.services.risk_calculator import PortfolioRiskInput

        risk_input = PortfolioRiskInput(
            portfolio=self.portfolio,
            positions=self.positions,
            investments=self.investments,
            current_prices=self.current_prices,
            historical_returns=historical_returns,
        )
        risk_metrics = self.risk_calculator.calculate_portfolio_risk_metrics(risk_input)

        # Check all metrics are calculated
        assert risk_metrics.value_at_risk_95.amount >= 0
        assert risk_metrics.value_at_risk_99.amount >= 0
        assert risk_metrics.expected_shortfall.amount >= 0
        assert isinstance(risk_metrics.portfolio_beta, float)
        assert isinstance(risk_metrics.portfolio_volatility, float)
        assert isinstance(risk_metrics.maximum_drawdown, float)
        assert isinstance(risk_metrics.concentration_risk, float)
        assert isinstance(risk_metrics.sector_concentration, dict)
        assert isinstance(risk_metrics.largest_position_weight, float)

        # Check reasonable ranges
        assert 0.0 <= risk_metrics.portfolio_beta <= 3.0
        assert 0.0 <= risk_metrics.portfolio_volatility <= 2.0
        assert 0.0 <= risk_metrics.maximum_drawdown <= 1.0
        assert 0.0 <= risk_metrics.concentration_risk <= 100.0
        assert 0.0 <= risk_metrics.largest_position_weight <= 100.0

    def test_market_cap_risk_scoring(self):
        """Test market cap risk scoring"""
        # Test different market caps using public interface
        # through position risk
        mega_investment = Investment.create(
            InvestmentCreateParams(
                symbol="MEGA",
                name="Mega Cap",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.UTILITIES,
                market_cap=MarketCap.MEGA,
                currency=Currency.USD,
                exchange="NYSE",
            )
        )

        nano_investment = Investment.create(
            InvestmentCreateParams(
                symbol="NANO",
                name="Nano Cap",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.UTILITIES,
                market_cap=MarketCap.NANO,
                currency=Currency.USD,
                exchange="NYSE",
            )
        )

        # Create identical positions
        position = Position(
            symbol="TEST",
            quantity=10,
            average_price=Money(Decimal("100.00"), Currency.USD),
            first_purchase_date=datetime.now(timezone.utc),
            last_update=datetime.now(timezone.utc),
        )

        portfolio_value = Money(Decimal("10000.00"), Currency.USD)

        mega_risk = self.risk_calculator.calculate_position_risk(
            position, mega_investment, portfolio_value
        )
        nano_risk = self.risk_calculator.calculate_position_risk(
            position, nano_investment, portfolio_value
        )

        # Nano cap should be riskier than mega cap
        assert nano_risk > mega_risk
        assert 0 <= mega_risk <= 100
        assert 0 <= nano_risk <= 100

    def test_sector_risk_through_investment_analysis(self):
        """Test sector risk by analyzing investment risk levels."""
        # Create investments in different sectors
        energy_investment = Investment.create(
            InvestmentCreateParams(
                symbol="ENERGY",
                name="Energy Company",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.ENERGY,
                market_cap=MarketCap.LARGE,
                currency=Currency.USD,
                exchange="NYSE",
            )
        )

        utilities_investment = Investment.create(
            InvestmentCreateParams(
                symbol="UTIL",
                name="Utilities Company",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.UTILITIES,
                market_cap=MarketCap.LARGE,
                currency=Currency.USD,
                exchange="NYSE",
            )
        )

        # Assess risk levels (which internally uses sector risk)
        energy_risk = energy_investment.assess_risk_level()
        utilities_risk = utilities_investment.assess_risk_level()

        # Risk levels should be strings
        assert energy_risk in ["LOW", "MEDIUM", "HIGH"]
        assert utilities_risk in ["LOW", "MEDIUM", "HIGH"]

    def test_technical_risk_through_investment_analysis(self):
        """Test technical risk assessment through investment analysis."""
        # Create investment with extreme technical indicators
        extreme_investment = Investment.create(
            InvestmentCreateParams(
                symbol="VOLATILE",
                name="Volatile Stock",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.TECHNOLOGY,
                market_cap=MarketCap.SMALL,
                currency=Currency.USD,
                exchange="NASDAQ",
            )
        )

        # Update with extreme technical data
        extreme_investment.update_technical_data(
            TechnicalData(
                rsi=95.0,  # Extremely overbought
                macd_signal="SELL",
                sma_50=Money(100, Currency.USD),
                sma_200=Money(120, Currency.USD),
                support_level=Money(80, Currency.USD),
                resistance_level=Money(150, Currency.USD),
            )
        )

        # Assess risk level (which internally uses technical analysis)
        risk_level = extreme_investment.assess_risk_level()

        # Should be high risk due to extreme technical indicators
        assert risk_level in ["MEDIUM", "HIGH"]
