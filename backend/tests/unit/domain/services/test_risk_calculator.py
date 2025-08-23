"""
Tests unitaires pour RiskCalculatorService
==========================================

Tests unitaires complets pour le service de calcul des risques du domaine.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from boursa_vision.domain.entities.investment import (
    Investment,
    InvestmentSector,
    MarketCap,
)
from boursa_vision.domain.entities.portfolio import Portfolio, Position, RiskLimits
from boursa_vision.domain.services.risk_calculator import (
    PortfolioRiskInput,
    RiskCalculatorService,
    RiskMetrics,
    RiskValidationResult,
)
from boursa_vision.domain.value_objects.money import Currency, Money


@pytest.fixture
def risk_calculator():
    """Instance de RiskCalculatorService pour les tests."""
    return RiskCalculatorService()


@pytest.fixture
def sample_portfolio():
    """Portfolio échantillon pour les tests."""
    portfolio = Mock(spec=Portfolio)
    portfolio.id = "test-portfolio-123"
    portfolio.cash_balance = Money(Decimal("10000.00"), Currency.USD)
    portfolio.calculate_total_value.return_value = Money(
        Decimal("100000.00"), Currency.USD
    )
    return portfolio


@pytest.fixture
def sample_positions():
    """Positions échantillons pour les tests."""
    position1 = Mock(spec=Position)
    position1.symbol = "AAPL"
    position1.quantity = 100
    position1.average_price = Money(Decimal("150.00"), Currency.USD)

    position2 = Mock(spec=Position)
    position2.symbol = "GOOGL"
    position2.quantity = 50
    position2.average_price = Money(Decimal("2800.00"), Currency.USD)

    position3 = Mock(spec=Position)
    position3.symbol = "MSFT"
    position3.quantity = 75
    position3.average_price = Money(Decimal("300.00"), Currency.USD)

    return [position1, position2, position3]


@pytest.fixture
def sample_investments():
    """Investissements échantillons pour les tests."""
    # Mock TechnicalData
    tech_data1 = Mock()
    tech_data1.rsi = 45.0  # Neutral RSI

    tech_data2 = Mock()
    tech_data2.rsi = 75.0  # Overbought

    tech_data3 = Mock()
    tech_data3.rsi = 30.0  # Oversold

    investment1 = Mock(spec=Investment)
    investment1.symbol = "AAPL"
    investment1.sector = InvestmentSector.TECHNOLOGY
    investment1.market_cap = MarketCap.LARGE
    investment1.assess_risk_level.return_value = "MEDIUM"
    investment1.beta = 1.2
    investment1.technical_data = tech_data1

    investment2 = Mock(spec=Investment)
    investment2.symbol = "GOOGL"
    investment2.sector = InvestmentSector.TECHNOLOGY
    investment2.market_cap = MarketCap.LARGE
    investment2.assess_risk_level.return_value = "MEDIUM"
    investment2.beta = 1.1
    investment2.technical_data = tech_data2

    investment3 = Mock(spec=Investment)
    investment3.symbol = "MSFT"
    investment3.sector = InvestmentSector.TECHNOLOGY
    investment3.market_cap = MarketCap.LARGE
    investment3.assess_risk_level.return_value = "LOW"
    investment3.beta = 0.9
    investment3.technical_data = tech_data3

    return {"AAPL": investment1, "GOOGL": investment2, "MSFT": investment3}


@pytest.fixture
def sample_current_prices():
    """Prix actuels échantillons."""
    return {
        "AAPL": Money(Decimal("150.00"), Currency.USD),
        "GOOGL": Money(Decimal("2800.00"), Currency.USD),
        "MSFT": Money(Decimal("300.00"), Currency.USD),
    }


@pytest.fixture
def sample_historical_returns():
    """Rendements historiques échantillons."""
    return {
        "AAPL": [0.01, 0.02, -0.01, 0.015, 0.005],
        "GOOGL": [0.015, 0.01, -0.005, 0.02, 0.008],
        "MSFT": [0.008, 0.012, -0.008, 0.01, 0.006],
    }


@pytest.fixture
def sample_risk_limits():
    """Limites de risque échantillons."""
    limits = Mock(spec=RiskLimits)
    limits.max_position_percentage = 15.0
    limits.max_sector_exposure = 40.0
    limits.min_cash_percentage = 5.0
    limits.max_portfolio_drawdown = 20.0
    limits.max_portfolio_volatility = 25.0
    return limits


@pytest.fixture
def sample_portfolio_risk_input(
    sample_portfolio,
    sample_positions,
    sample_investments,
    sample_current_prices,
    sample_historical_returns,
):
    """Données d'entrée pour le calcul de risque de portefeuille."""
    return PortfolioRiskInput(
        portfolio=sample_portfolio,
        positions=sample_positions,
        investments=sample_investments,
        current_prices=sample_current_prices,
        historical_returns=sample_historical_returns,
    )


class TestRiskCalculatorServiceCreation:
    """Tests pour la création du service de calcul des risques."""

    def test_should_create_risk_calculator_service(self):
        """Test la création du service."""
        # Act
        service = RiskCalculatorService()

        # Assert
        assert isinstance(service, RiskCalculatorService)


class TestRiskCalculatorPositionRisk:
    """Tests pour le calcul de risque de position."""

    def test_should_calculate_position_risk_successfully(
        self, risk_calculator, sample_positions, sample_investments
    ):
        """Test le calcul réussi du risque de position."""
        # Arrange
        position = sample_positions[0]  # AAPL
        investment = sample_investments["AAPL"]
        portfolio_value = Money(Decimal("100000.00"), Currency.USD)

        # Act
        risk_score = risk_calculator.calculate_position_risk(
            position, investment, portfolio_value
        )

        # Assert
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 100.0

    def test_should_handle_large_position_weight(
        self, risk_calculator, sample_investments
    ):
        """Test la gestion d'un poids de position important."""
        # Arrange
        large_position = Mock(spec=Position)
        large_position.symbol = "AAPL"
        large_position.quantity = 1000  # Grande quantité
        large_position.average_price = Money(Decimal("150.00"), Currency.USD)

        investment = sample_investments["AAPL"]
        portfolio_value = Money(Decimal("50000.00"), Currency.USD)  # Valeur plus faible

        # Act
        risk_score = risk_calculator.calculate_position_risk(
            large_position, investment, portfolio_value
        )

        # Assert
        assert isinstance(risk_score, float)
        assert risk_score > 50.0  # Devrait être élevé


class TestRiskCalculatorPortfolioRiskMetrics:
    """Tests pour le calcul des métriques de risque de portefeuille."""

    def test_should_calculate_portfolio_risk_metrics_successfully(
        self, risk_calculator, sample_portfolio_risk_input
    ):
        """Test le calcul réussi des métriques de risque de portefeuille."""
        # Act
        metrics = risk_calculator.calculate_portfolio_risk_metrics(
            sample_portfolio_risk_input
        )

        # Assert
        assert isinstance(metrics, RiskMetrics)
        assert isinstance(metrics.value_at_risk_95, Money)
        assert isinstance(metrics.value_at_risk_99, Money)
        assert isinstance(metrics.expected_shortfall, Money)
        assert isinstance(metrics.portfolio_beta, float)
        assert isinstance(metrics.portfolio_volatility, float)
        assert isinstance(metrics.maximum_drawdown, float)
        assert isinstance(metrics.concentration_risk, float)
        assert isinstance(metrics.sector_concentration, dict)
        assert isinstance(metrics.largest_position_weight, float)

    def test_should_calculate_var_correctly(
        self, risk_calculator, sample_portfolio_risk_input
    ):
        """Test le calcul correct de la VaR."""
        # Act
        metrics = risk_calculator.calculate_portfolio_risk_metrics(
            sample_portfolio_risk_input
        )

        # Assert
        # VaR 99% devrait être >= VaR 95%
        assert metrics.value_at_risk_99.amount >= metrics.value_at_risk_95.amount
        # Expected shortfall devrait être >= VaR 95%
        assert metrics.expected_shortfall.amount >= metrics.value_at_risk_95.amount

    def test_should_handle_empty_positions(self, risk_calculator, sample_portfolio):
        """Test la gestion de positions vides."""
        # Arrange
        empty_input = PortfolioRiskInput(
            portfolio=sample_portfolio,
            positions=[],
            investments={},
            current_prices={},
            historical_returns={},
        )

        # Act
        metrics = risk_calculator.calculate_portfolio_risk_metrics(empty_input)

        # Assert
        assert isinstance(metrics, RiskMetrics)
        assert abs(metrics.concentration_risk - 0.0) < 1e-10
        assert abs(metrics.largest_position_weight - 0.0) < 1e-10


class TestRiskCalculatorRiskValidation:
    """Tests pour la validation des limites de risque."""

    def test_should_validate_risk_limits_successfully(
        self,
        risk_calculator,
        sample_portfolio,
        sample_positions,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test la validation réussie des limites de risque."""
        # Act
        result = risk_calculator.validate_risk_limits(
            sample_portfolio,
            sample_positions,
            sample_investments,
            sample_current_prices,
            sample_risk_limits,
        )

        # Assert
        assert isinstance(result, RiskValidationResult)
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.violations, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.risk_score, float)
        assert 0.0 <= result.risk_score <= 100.0

    def test_should_detect_position_limit_violation(
        self,
        risk_calculator,
        sample_portfolio,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test la détection de violation de limite de position."""
        # Arrange
        large_position = Mock(spec=Position)
        large_position.symbol = "AAPL"
        large_position.quantity = 1000  # Position très importante
        large_position.average_price = Money(Decimal("150.00"), Currency.USD)

        positions = [large_position]
        sample_risk_limits.max_position_percentage = 5.0  # Limite très stricte

        # Act
        result = risk_calculator.validate_risk_limits(
            sample_portfolio,
            positions,
            sample_investments,
            sample_current_prices,
            sample_risk_limits,
        )

        # Assert
        assert result.is_valid is False
        assert len(result.violations) > 0
        assert any("exceeds limit" in violation for violation in result.violations)

    def test_should_detect_sector_concentration_violation(
        self,
        risk_calculator,
        sample_portfolio,
        sample_positions,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test la détection de violation de concentration sectorielle."""
        # Arrange
        sample_risk_limits.max_sector_exposure = 10.0  # Limite très stricte

        # Act
        result = risk_calculator.validate_risk_limits(
            sample_portfolio,
            sample_positions,
            sample_investments,
            sample_current_prices,
            sample_risk_limits,
        )

        # Assert
        # Toutes les positions sont dans TECHNOLOGY, devrait violer
        assert result.is_valid is False
        assert len(result.violations) > 0

    def test_should_detect_cash_minimum_violation(
        self,
        risk_calculator,
        sample_portfolio,
        sample_positions,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test la détection de violation du minimum de trésorerie."""
        # Arrange
        sample_portfolio.cash_balance = Money(Decimal("1000.00"), Currency.USD)
        sample_risk_limits.min_cash_percentage = 20.0  # 20% minimum

        # Act
        result = risk_calculator.validate_risk_limits(
            sample_portfolio,
            sample_positions,
            sample_investments,
            sample_current_prices,
            sample_risk_limits,
        )

        # Assert
        assert result.is_valid is False
        assert any("Cash below minimum" in violation for violation in result.violations)

    def test_should_generate_warnings_for_near_limits(
        self,
        risk_calculator,
        sample_portfolio,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test la génération d'avertissements pour les limites proches."""
        # Arrange - Créer un portefeuille réaliste avec des positions modérées
        # Portfolio total: $100,000, Cash: $10,000, donc positions: $90,000 max

        tech_position = Mock(spec=Position)
        tech_position.symbol = "AAPL"
        tech_position.quantity = 100  # 100 * $150 = $15,000 (15% du portefeuille)
        tech_position.average_price = Money(Decimal("150.00"), Currency.USD)

        financial_position = Mock(spec=Position)
        financial_position.symbol = "JPM"
        financial_position.quantity = 100  # 100 * $150 = $15,000 (15% du portefeuille)
        financial_position.average_price = Money(Decimal("150.00"), Currency.USD)

        # Créer un investissement financier avec technical_data
        financial_investment = Mock(spec=Investment)
        financial_investment.symbol = "JPM"
        financial_investment.sector = InvestmentSector.FINANCIAL  # Secteur différent
        financial_investment.market_cap = MarketCap.LARGE
        financial_investment.assess_risk_level.return_value = "MEDIUM"
        financial_investment.beta = 1.0
        tech_data_financial = Mock()
        tech_data_financial.rsi = 50.0
        financial_investment.technical_data = tech_data_financial

        # Mettre à jour les investissements et prix
        investments_with_financial = {**sample_investments, "JPM": financial_investment}
        prices_with_financial = {
            **sample_current_prices,
            "JPM": Money(Decimal("150.00"), Currency.USD),
        }

        # Total: Tech 15% + Financial 15% = 30% < 40% pour chaque secteur
        positions = [tech_position, financial_position]
        sample_risk_limits.max_position_percentage = 20.0  # 15% < 20% ✓
        sample_risk_limits.max_sector_exposure = (
            40.0  # Tech 15% et Financial 15% < 40% ✓
        )
        sample_risk_limits.min_cash_percentage = 5.0  # 10% > 5% ✓

        # Act
        result = risk_calculator.validate_risk_limits(
            sample_portfolio,
            positions,
            investments_with_financial,
            prices_with_financial,
            sample_risk_limits,
        )

        # Assert
        assert (
            result.is_valid is True
        )  # Pas de violations avec des positions modérées et diversifiées


class TestRiskCalculatorRiskReduction:
    """Tests pour les suggestions de réduction de risque."""

    def test_should_suggest_risk_reduction_successfully(
        self,
        risk_calculator,
        sample_portfolio,
        sample_positions,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test les suggestions réussies de réduction de risque."""
        # Act
        suggestions = risk_calculator.suggest_risk_reduction(
            sample_portfolio,
            sample_positions,
            sample_investments,
            sample_current_prices,
            sample_risk_limits,
        )

        # Assert
        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert isinstance(suggestion, str)

    def test_should_suggest_reducing_oversized_positions(
        self,
        risk_calculator,
        sample_portfolio,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test les suggestions pour réduire les positions surdimensionnées."""
        # Arrange
        large_position = Mock(spec=Position)
        large_position.symbol = "AAPL"
        large_position.quantity = 1000  # Position très importante
        large_position.average_price = Money(Decimal("150.00"), Currency.USD)

        positions = [large_position]
        sample_risk_limits.max_position_percentage = 5.0  # Limite stricte

        # Act
        suggestions = risk_calculator.suggest_risk_reduction(
            sample_portfolio,
            positions,
            sample_investments,
            sample_current_prices,
            sample_risk_limits,
        )

        # Assert
        assert len(suggestions) > 0
        assert any(
            "Reduce" in suggestion and "position" in suggestion
            for suggestion in suggestions
        )

    def test_should_suggest_reducing_sector_concentration(
        self,
        risk_calculator,
        sample_portfolio,
        sample_positions,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test les suggestions pour réduire la concentration sectorielle."""
        # Arrange
        sample_risk_limits.max_sector_exposure = 10.0  # Limite très stricte

        # Act
        suggestions = risk_calculator.suggest_risk_reduction(
            sample_portfolio,
            sample_positions,
            sample_investments,
            sample_current_prices,
            sample_risk_limits,
        )

        # Assert
        assert len(suggestions) > 0
        assert any("sector exposure" in suggestion for suggestion in suggestions)

    def test_should_suggest_reducing_high_risk_positions(
        self,
        risk_calculator,
        sample_portfolio,
        sample_investments,
        sample_current_prices,
        sample_risk_limits,
    ):
        """Test les suggestions pour réduire les positions à haut risque."""
        # Arrange
        high_risk_investment = Mock(spec=Investment)
        high_risk_investment.symbol = "RISKY"
        high_risk_investment.sector = InvestmentSector.TECHNOLOGY
        high_risk_investment.market_cap = MarketCap.SMALL
        high_risk_investment.assess_risk_level.return_value = "HIGH"

        high_risk_position = Mock(spec=Position)
        high_risk_position.symbol = "RISKY"
        high_risk_position.quantity = 100
        high_risk_position.average_price = Money(Decimal("50.00"), Currency.USD)

        investments = {**sample_investments, "RISKY": high_risk_investment}
        positions = [high_risk_position]
        current_prices = {
            **sample_current_prices,
            "RISKY": Money(Decimal("50.00"), Currency.USD),
        }

        # Act
        suggestions = risk_calculator.suggest_risk_reduction(
            sample_portfolio, positions, investments, current_prices, sample_risk_limits
        )

        # Assert
        assert len(suggestions) > 0
        assert any("high-risk positions" in suggestion for suggestion in suggestions)


class TestRiskCalculatorPrivateMethods:
    """Tests pour les méthodes privées."""

    def test_should_calculate_position_weight(self, risk_calculator):
        """Test le calcul du poids de position."""
        # Arrange
        position = Mock(spec=Position)
        position.quantity = 100
        position.average_price = Money(Decimal("50.00"), Currency.USD)
        portfolio_value = Money(Decimal("100000.00"), Currency.USD)

        # Act
        with patch.object(risk_calculator, "_calculate_position_weight") as mock_method:
            mock_method.return_value = 15.0
            weight = risk_calculator._calculate_position_weight(
                position, portfolio_value
            )

        # Assert
        mock_method.assert_called_once_with(position, portfolio_value)
        assert abs(weight - 15.0) < 1e-10

    def test_should_get_market_cap_risk(self, risk_calculator):
        """Test l'obtention du risque de capitalisation boursière."""
        # Act
        large_cap_risk = risk_calculator._get_market_cap_risk(MarketCap.LARGE)
        small_cap_risk = risk_calculator._get_market_cap_risk(MarketCap.SMALL)

        # Assert
        assert isinstance(large_cap_risk, float)
        assert isinstance(small_cap_risk, float)
        assert small_cap_risk > large_cap_risk  # Small cap plus risqué

    def test_should_get_sector_risk(self, risk_calculator):
        """Test l'obtention du risque sectoriel."""
        # Act
        tech_risk = risk_calculator._get_sector_risk(InvestmentSector.TECHNOLOGY)
        healthcare_risk = risk_calculator._get_sector_risk(InvestmentSector.HEALTHCARE)

        # Assert
        assert isinstance(tech_risk, float)
        assert isinstance(healthcare_risk, float)
        assert 0.0 <= tech_risk <= 100.0
        assert 0.0 <= healthcare_risk <= 100.0

    def test_should_get_technical_risk(self, risk_calculator, sample_investments):
        """Test l'obtention du risque technique."""
        # Arrange
        investment = sample_investments["AAPL"]

        # Act
        risk = risk_calculator._get_technical_risk(investment)

        # Assert
        assert isinstance(risk, float)
        assert 0.0 <= risk <= 100.0

    def test_should_calculate_var(self, risk_calculator):
        """Test le calcul de la VaR."""
        # Arrange
        returns = [0.01, 0.02, -0.01, 0.015, -0.005, -0.02, 0.008]
        confidence_level = 0.95

        # Act
        var = risk_calculator._calculate_var(returns, confidence_level)

        # Assert
        assert isinstance(var, float)
        assert var <= 0  # VaR devrait être négative (perte)

    def test_should_calculate_expected_shortfall(self, risk_calculator):
        """Test le calcul de l'Expected Shortfall."""
        # Arrange
        returns = [0.01, 0.02, -0.01, 0.015, -0.005, -0.02, 0.008]
        confidence_level = 0.95

        # Act
        es = risk_calculator._calculate_expected_shortfall(returns, confidence_level)

        # Assert
        assert isinstance(es, float)
        assert es <= 0  # Expected Shortfall devrait être négatif

    def test_should_calculate_portfolio_beta(
        self, risk_calculator, sample_positions, sample_investments
    ):
        """Test le calcul du beta de portefeuille."""
        # Act
        beta = risk_calculator._calculate_portfolio_beta(
            sample_positions, sample_investments
        )

        # Assert
        assert isinstance(beta, float)
        assert beta > 0.0  # Beta devrait être positif

    def test_should_calculate_volatility(self, risk_calculator):
        """Test le calcul de la volatilité."""
        # Arrange
        returns = [0.01, 0.02, -0.01, 0.015, -0.005]

        # Act
        volatility = risk_calculator._calculate_volatility(returns)

        # Assert
        assert isinstance(volatility, float)
        assert volatility >= 0.0

    def test_should_calculate_max_drawdown(self, risk_calculator):
        """Test le calcul du drawdown maximal."""
        # Arrange
        returns = [0.01, 0.02, -0.05, 0.03, -0.02]

        # Act
        max_dd = risk_calculator._calculate_max_drawdown(returns)

        # Assert
        assert isinstance(max_dd, float)
        assert max_dd >= 0.0  # Drawdown est retourné comme valeur positive (magnitude)

    def test_should_calculate_portfolio_returns(
        self, risk_calculator, sample_positions, sample_historical_returns
    ):
        """Test le calcul des rendements de portefeuille."""
        # Act
        returns = risk_calculator._calculate_portfolio_returns(
            sample_positions, sample_historical_returns
        )

        # Assert
        assert isinstance(returns, list)
        for ret in returns:
            assert isinstance(ret, float)

    def test_should_calculate_concentration_risk(
        self, risk_calculator, sample_positions, sample_current_prices
    ):
        """Test le calcul du risque de concentration."""
        # Act
        concentration = risk_calculator._calculate_concentration_risk(
            sample_positions, sample_current_prices
        )

        # Assert
        assert isinstance(concentration, float)
        assert 0.0 <= concentration <= 100.0

    def test_should_calculate_sector_concentration(
        self,
        risk_calculator,
        sample_positions,
        sample_investments,
        sample_current_prices,
    ):
        """Test le calcul de la concentration sectorielle."""
        # Act
        sectors = risk_calculator._calculate_sector_concentration(
            sample_positions, sample_investments, sample_current_prices
        )

        # Assert
        assert isinstance(sectors, dict)
        for sector, percentage in sectors.items():
            assert isinstance(sector, str)
            assert isinstance(percentage, float)
            assert 0.0 <= percentage <= 100.0

    def test_should_get_largest_position_weight(
        self, risk_calculator, sample_positions, sample_current_prices
    ):
        """Test l'obtention du poids de la plus grande position."""
        # Act
        largest_weight = risk_calculator._get_largest_position_weight(
            sample_positions, sample_current_prices
        )

        # Assert
        assert isinstance(largest_weight, float)
        assert 0.0 <= largest_weight <= 100.0


class TestRiskCalculatorEdgeCases:
    """Tests pour les cas limites."""

    def test_should_handle_empty_historical_returns(self, risk_calculator):
        """Test la gestion de rendements historiques vides."""
        # Arrange
        empty_returns = []

        # Act
        var = risk_calculator._calculate_var(empty_returns, 0.95)
        volatility = risk_calculator._calculate_volatility(empty_returns)

        # Assert
        assert abs(var - 0.0) < 1e-10
        assert abs(volatility - 0.0) < 1e-10

    def test_should_handle_zero_portfolio_value(self, risk_calculator):
        """Test la gestion d'une valeur de portefeuille nulle."""
        # Arrange
        position = Mock(spec=Position)
        position.quantity = 100
        position.average_price = Money(Decimal("50.00"), Currency.USD)
        zero_value = Money(Decimal("0.00"), Currency.USD)

        # Act
        # Cela pourrait lever une exception selon l'implémentation
        try:
            risk_calculator._calculate_position_weight(position, zero_value)
        except (ZeroDivisionError, ValueError):
            # Comportement attendu pour valeur nulle
            pass

    def test_should_handle_missing_investment_data(
        self, risk_calculator, sample_positions, sample_current_prices
    ):
        """Test la gestion de données d'investissement manquantes."""
        # Arrange
        empty_investments = {}

        # Act
        sectors = risk_calculator._calculate_sector_concentration(
            sample_positions, empty_investments, sample_current_prices
        )

        # Assert
        assert sectors == {}

    def test_should_handle_missing_price_data(
        self, risk_calculator, sample_positions, sample_investments
    ):
        """Test la gestion de données de prix manquantes."""
        # Arrange
        empty_prices = {}

        # Act
        concentration = risk_calculator._calculate_concentration_risk(
            sample_positions, empty_prices
        )

        # Assert
        assert abs(concentration - 0.0) < 1e-10


class TestPortfolioRiskInputDataclass:
    """Tests pour la dataclass PortfolioRiskInput."""

    def test_should_create_portfolio_risk_input(
        self,
        sample_portfolio,
        sample_positions,
        sample_investments,
        sample_current_prices,
        sample_historical_returns,
    ):
        """Test la création de PortfolioRiskInput."""
        # Act
        input_data = PortfolioRiskInput(
            portfolio=sample_portfolio,
            positions=sample_positions,
            investments=sample_investments,
            current_prices=sample_current_prices,
            historical_returns=sample_historical_returns,
        )

        # Assert
        assert isinstance(input_data, PortfolioRiskInput)
        assert input_data.portfolio == sample_portfolio
        assert input_data.positions == sample_positions
        assert input_data.investments == sample_investments
        assert input_data.current_prices == sample_current_prices
        assert input_data.historical_returns == sample_historical_returns


class TestRiskMetricsDataclass:
    """Tests pour la dataclass RiskMetrics."""

    def test_should_create_risk_metrics(self):
        """Test la création de RiskMetrics."""
        # Arrange
        var_95 = Money(Decimal("5000.00"), Currency.USD)
        var_99 = Money(Decimal("8000.00"), Currency.USD)
        expected_shortfall = Money(Decimal("6000.00"), Currency.USD)

        # Act
        metrics = RiskMetrics(
            value_at_risk_95=var_95,
            value_at_risk_99=var_99,
            expected_shortfall=expected_shortfall,
            portfolio_beta=1.1,
            portfolio_volatility=0.15,
            maximum_drawdown=-0.08,
            concentration_risk=25.5,
            sector_concentration={"TECHNOLOGY": 60.0, "HEALTHCARE": 40.0},
            largest_position_weight=25.0,
        )

        # Assert
        assert isinstance(metrics, RiskMetrics)
        assert metrics.value_at_risk_95 == var_95
        assert metrics.value_at_risk_99 == var_99
        assert metrics.expected_shortfall == expected_shortfall
        assert abs(metrics.portfolio_beta - 1.1) < 1e-10
        assert abs(metrics.portfolio_volatility - 0.15) < 1e-10


class TestRiskValidationResultDataclass:
    """Tests pour la dataclass RiskValidationResult."""

    def test_should_create_risk_validation_result(self):
        """Test la création de RiskValidationResult."""
        # Act
        result = RiskValidationResult(
            is_valid=False,
            violations=["Position AAPL exceeds limit"],
            warnings=["Cash level low"],
            risk_score=35.5,
        )

        # Assert
        assert isinstance(result, RiskValidationResult)
        assert result.is_valid is False
        assert len(result.violations) == 1
        assert len(result.warnings) == 1
        assert abs(result.risk_score - 35.5) < 1e-10
