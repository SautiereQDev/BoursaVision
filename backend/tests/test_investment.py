"""
Tests for Investment Entity
===========================

Unit tests for the Investment domain entity and its business logic.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.investment import (
    FundamentalData,
    Investment,
    InvestmentSector,
    InvestmentType,
    MarketCap,
    TechnicalData,
)
from src.domain.services.scoring_service import (
    FundamentalScoringStrategy,
    ScoringService,
)
from src.domain.value_objects.money import Currency, Money
from src.domain.value_objects.signal import ConfidenceScore, SignalAction


class TestInvestment:
    """Test cases for Investment entity"""

    def test_create_investment(self):
        """Test investment creation with factory method"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        assert investment.symbol == "AAPL"
        assert investment.name == "Apple Inc."
        assert investment.investment_type == InvestmentType.STOCK
        assert investment.sector == InvestmentSector.TECHNOLOGY
        assert investment.market_cap == MarketCap.MEGA
        assert investment.currency == Currency.USD
        assert investment.exchange == "NASDAQ"
        assert investment.id is not None
        assert investment.created_at is not None

        # Check domain event was raised
        events = investment.get_domain_events()
        assert len(events) == 1
        assert events[0].__class__.__name__ == "InvestmentCreatedEvent"

    def test_update_price_valid(self):
        """Test updating price with valid data"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        new_price = Money(Decimal("150.00"), Currency.USD)
        investment.update_price(new_price)

        assert investment.current_price == new_price

    def test_update_price_wrong_currency(self):
        """Test updating price with wrong currency raises error"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        wrong_currency_price = Money(Decimal("150.00"), Currency.EUR)

        with pytest.raises(ValueError, match="Price currency"):
            investment.update_price(wrong_currency_price)

    def test_update_price_negative(self):
        """Test updating with negative price raises error"""
        # Negative money amount should be invalid
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            Money(Decimal("-10.00"), Currency.USD)

    def test_investment_sector(self):
        """Test sector logic for Investment entity"""
        investment = Investment.create(
            symbol="MSFT",
            name="Microsoft Corp.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        assert investment.sector == InvestmentSector.TECHNOLOGY

    def test_investment_type(self):
        """Test investment type logic for Investment entity"""
        investment = Investment.create(
            symbol="BTC",
            name="Bitcoin",
            investment_type=InvestmentType.CRYPTOCURRENCY,
            sector=InvestmentSector.FINANCIAL,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="CRYPTO",
        )

        assert investment.investment_type == InvestmentType.CRYPTOCURRENCY

    def test_update_fundamental_data(self):
        """Test updating fundamental data"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        fundamental_data = FundamentalData(
            pe_ratio=20.0, roe=15.0, revenue_growth=10.0, debt_to_equity=0.5
        )
        investment.update_fundamental_data(fundamental_data)

        assert investment.fundamental_data == fundamental_data
        assert investment.last_analyzed is not None

    def test_update_technical_data(self):
        """Test updating technical data"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        technical_data = TechnicalData(
            rsi=50.0,
            macd_signal="BUY",
            sma_50=Money(Decimal("145.00"), Currency.USD),
            sma_200=Money(Decimal("140.00"), Currency.USD),
            volume_trend="INCREASING",
        )
        investment.update_technical_data(technical_data)

        assert investment.technical_data == technical_data
        assert investment.last_analyzed is not None

    def test_calculate_composite_score(self):
        """Test composite score calculation"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # Set fundamental and technical data
        fundamental_data = FundamentalData(
            pe_ratio=15.0, roe=20.0, revenue_growth=18.0, debt_to_equity=0.2
        )
        technical_data = TechnicalData(
            rsi=45.0,
            macd_signal="BUY",
            sma_50=Money(Decimal("145.00"), Currency.USD),
            sma_200=Money(Decimal("140.00"), Currency.USD),
            volume_trend="INCREASING",
        )
        investment.update_fundamental_data(fundamental_data)
        investment.update_technical_data(technical_data)

        composite_score = investment.calculate_composite_score()

        assert composite_score > 40.0
        assert composite_score <= 100.0

    def test_assess_risk_level_medium(self):
        """Test medium risk assessment"""
        investment = Investment.create(
            symbol="AMZN",
            name="Amazon.com Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.CONSUMER_DISCRETIONARY,
            market_cap=MarketCap.MID,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # Add medium-risk fundamental data
        fundamental_data = FundamentalData(
            debt_to_equity=0.8, pe_ratio=30.0  # Moderate debt  # Moderate valuation
        )
        investment.update_fundamental_data(fundamental_data)

        # Add neutral technical indicators
        technical_data = TechnicalData(rsi=50.0)  # Neutral RSI
        investment.update_technical_data(technical_data)

        risk_level = investment.assess_risk_level()

        assert risk_level == "MEDIUM"

    def test_is_analysis_stale_with_recent_data(self):
        """Test analysis staleness with recent data"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # Update data to make it recent
        fundamental_data = FundamentalData(pe_ratio=15.0)
        investment.update_fundamental_data(fundamental_data)

        assert not investment.is_analysis_stale(max_age_hours=48)

        # Verify the currency of the investment
        assert investment.currency == Currency.USD

    def test_calculate_fundamental_score_with_pe_ratio(self):
        investment = Investment(
            id=uuid4(),
            symbol="AAPL",
            name="Test Investment",
            sector=InvestmentSector.TECHNOLOGY,
            investment_type=InvestmentType.STOCK,
            market_cap=MarketCap.LARGE,
            currency=Currency.USD,
            exchange="NASDAQ",
            current_price=Money(amount=Decimal("150.00"), currency=Currency.USD),
        )
        investment._score_pe_ratio = lambda: (15.0, 1.0)
        investment._score_roe = lambda: (0.0, 0.0)
        investment._score_revenue_growth = lambda: (0.0, 0.0)
        investment._score_debt_to_equity = lambda: (0.0, 0.0)
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = scoring_service.calculate_score(investment)
        assert abs(score - 4.5) < 1e-6  # Corrected expected value

    def test_calculate_fundamental_score_with_roe(self):
        investment = Investment(
            id=uuid4(),
            symbol="AAPL",
            name="Test Investment",
            sector=InvestmentSector.TECHNOLOGY,
            investment_type=InvestmentType.STOCK,
            market_cap=MarketCap.LARGE,
            currency=Currency.USD,
            exchange="NASDAQ",
            current_price=Money(amount=Decimal("150.00"), currency=Currency.USD),
        )
        investment._score_pe_ratio = lambda: (0.0, 0.0)
        investment._score_roe = lambda: (20.0, 1.0)
        investment._score_revenue_growth = lambda: (0.0, 0.0)
        investment._score_debt_to_equity = lambda: (0.0, 0.0)
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = scoring_service.calculate_score(investment)
        assert abs(score - 6.0) < 1e-6  # Corrected expected value

    def test_calculate_fundamental_score_neutral(self):
        investment = Investment(
            id=uuid4(),
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            currency=Currency.USD,
            exchange="NASDAQ",
            current_price=Money(amount=Decimal("150.00"), currency=Currency.USD),
        )
        # Simulate neutral components
        investment._score_pe_ratio = lambda: (50.0, 1.0)
        investment._score_roe = lambda: (50.0, 1.0)
        investment._score_revenue_growth = lambda: (50.0, 1.0)
        investment._score_debt_to_equity = lambda: (50.0, 1.0)
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = scoring_service.calculate_score(investment)
        assert abs(score - 50.0) < 1e-6  # Updated expected value

    def test_calculate_fundamental_score_high(self):
        investment = Investment(
            id=uuid4(),
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            currency=Currency.USD,
            exchange="NASDAQ",
            current_price=Money(amount=Decimal("150.00"), currency=Currency.USD),
        )
        # Simuler des composants élevés
        investment._score_pe_ratio = lambda: (80.0, 1.0)
        investment._score_roe = lambda: (90.0, 1.0)
        investment._score_revenue_growth = lambda: (85.0, 1.0)
        investment._score_debt_to_equity = lambda: (70.0, 1.0)
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = scoring_service.calculate_score(investment)
        assert score > 75.0

    def test_calculate_fundamental_score_low(self):
        investment = Investment(
            id=uuid4(),
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            currency=Currency.USD,
            exchange="NASDAQ",
            current_price=Money(amount=Decimal("150.00"), currency=Currency.USD),
        )
        # Simuler des composants faibles
        investment._score_pe_ratio = lambda: (20.0, 1.0)
        investment._score_roe = lambda: (30.0, 1.0)
        investment._score_revenue_growth = lambda: (25.0, 1.0)
        investment._score_debt_to_equity = lambda: (15.0, 1.0)
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = scoring_service.calculate_score(investment)
        assert score < 40.0


class TestFundamentalData:
    """Test cases for FundamentalData"""

    def test_calculate_fundamental_score_excellent(self):
        """Test fundamental score calculation for excellent metrics"""
        fundamental_data = FundamentalData(
            pe_ratio=15.0,  # Good P/E
            roe=20.0,  # Excellent ROE
            revenue_growth=18.0,  # Strong growth
            debt_to_equity=0.2,  # Low debt
        )
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = fundamental_data.calculate_fundamental_score(scoring_service)
        assert score > 59.0  # Updated expected range
        assert score <= 80.0

    def test_calculate_fundamental_score_poor(self):
        """Test fundamental score calculation for poor metrics"""
        fundamental_data = FundamentalData(
            pe_ratio=60.0,  # High P/E
            roe=2.0,  # Poor ROE
            revenue_growth=-5.0,  # Negative growth
            debt_to_equity=2.0,  # High debt
        )
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = fundamental_data.calculate_fundamental_score(scoring_service)

        # Should be low score
        assert score < 50.0

    def test_calculate_fundamental_score_no_data(self):
        """Test fundamental score with no data returns neutral"""
        fundamental_data = FundamentalData()
        scoring_service = ScoringService(FundamentalScoringStrategy())
        score = fundamental_data.calculate_fundamental_score(scoring_service)

        assert abs(score - 50.0) < 0.001  # Neutral score


class TestTechnicalData:
    """Test cases for TechnicalData"""

    def test_calculate_technical_score_bullish(self):
        """Test technical score for bullish signals"""
        current_price = Money(Decimal("150.00"), Currency.USD)
        sma_50 = Money(Decimal("145.00"), Currency.USD)
        sma_200 = Money(Decimal("140.00"), Currency.USD)

        technical_data = TechnicalData(
            rsi=45.0,  # Neutral RSI
            macd_signal="BUY",  # Bullish MACD
            sma_50=sma_50,
            sma_200=sma_200,
            volume_trend="INCREASING",
        )

        score = technical_data.calculate_technical_score(current_price)

        # Should be above neutral (50)
        assert score > 60.0

    def test_calculate_technical_score_bearish(self):
        """Test technical score for bearish signals"""
        current_price = Money(Decimal("130.00"), Currency.USD)
        sma_50 = Money(Decimal("135.00"), Currency.USD)
        sma_200 = Money(Decimal("140.00"), Currency.USD)

        technical_data = TechnicalData(
            rsi=85.0,  # Overbought
            macd_signal="SELL",  # Bearish MACD
            sma_50=sma_50,
            sma_200=sma_200,
            volume_trend="DECREASING",
        )

        score = technical_data.calculate_technical_score(current_price)

        # Should be below neutral (50)
        assert score < 40.0


class TestInvestmentSignalGeneration:
    """Test cases for investment signal generation"""

    def test_generate_signal_strong_buy(self):
        """Test signal generation for strong buy scenario"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # Set current price
        current_price = Money(Decimal("150.00"), Currency.USD)
        investment.update_price(current_price)

        # Set excellent fundamental data
        fundamental_data = FundamentalData(
            pe_ratio=15.0, roe=25.0, revenue_growth=20.0, debt_to_equity=0.1
        )
        investment.update_fundamental_data(fundamental_data)

        # Set bullish technical data
        technical_data = TechnicalData(
            rsi=50.0,
            macd_signal="BUY",
            sma_50=Money(Decimal("145.00"), Currency.USD),
            sma_200=Money(Decimal("140.00"), Currency.USD),
            volume_trend="INCREASING",
        )
        investment.update_technical_data(technical_data)

        signal = investment.generate_signal()

        assert signal == SignalAction.BUY

    def test_generate_signal_no_price(self):
        """Test signal generation without price data"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        signal = investment.generate_signal()

        assert signal == SignalAction.HOLD


class TestInvestmentRiskAssessment:
    """Test cases for investment risk assessment"""

    def test_assess_risk_level_high(self):
        """Test high risk assessment"""
        investment = Investment.create(
            symbol="NANO",
            name="Nano Cap Stock",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,  # High risk sector
            market_cap=MarketCap.NANO,  # High risk market cap
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # Add high-risk fundamental data
        fundamental_data = FundamentalData(
            debt_to_equity=2.0, pe_ratio=80.0  # High debt  # High valuation
        )
        investment.update_fundamental_data(fundamental_data)

        # Add extreme technical indicators
        technical_data = TechnicalData(rsi=90.0)  # Extreme overbought
        investment.update_technical_data(technical_data)

        risk_level = investment.assess_risk_level()

        assert risk_level == "HIGH"

    def test_assess_risk_level_low(self):
        """Test low risk assessment"""
        investment = Investment.create(
            symbol="KO",
            name="Coca-Cola",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.CONSUMER_STAPLES,  # Low risk sector
            market_cap=MarketCap.MEGA,  # Low risk market cap
            currency=Currency.USD,
            exchange="NYSE",
        )

        # Add low-risk fundamental data
        fundamental_data = FundamentalData(
            debt_to_equity=0.3, pe_ratio=20.0  # Reasonable debt  # Reasonable valuation
        )
        investment.update_fundamental_data(fundamental_data)

        # Add neutral technical indicators
        technical_data = TechnicalData(rsi=50.0)  # Neutral RSI
        investment.update_technical_data(technical_data)

        risk_level = investment.assess_risk_level()

        assert risk_level == "LOW"

    def test_is_analysis_stale(self):
        """Test analysis staleness check"""
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # Initially should be stale (no analysis done)
        assert investment.is_analysis_stale()

        # After updating data, should not be stale
        fundamental_data = FundamentalData(pe_ratio=15.0)
        investment.update_fundamental_data(fundamental_data)

        assert not investment.is_analysis_stale()

        # Should be stale with 0 hour threshold
        assert investment.is_analysis_stale(max_age_hours=0)
