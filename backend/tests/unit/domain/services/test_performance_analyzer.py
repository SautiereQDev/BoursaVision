"""
Tests unitaires pour PerformanceAnalyzerService
==============================================

Tests unitaires complets pour le service d'analyse de performance du domaine.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from boursa_vision.domain.entities.portfolio import PerformanceMetrics, Portfolio
from boursa_vision.domain.services.performance_analyzer import (
    PerformanceAnalyzerService,
    PerformanceComparison,
    RiskAdjustedMetrics,
)
from boursa_vision.domain.value_objects.money import Currency, Money


@pytest.fixture
def performance_analyzer():
    """Instance de PerformanceAnalyzerService pour les tests."""
    return PerformanceAnalyzerService()


@pytest.fixture
def sample_portfolio():
    """Portfolio échantillon pour les tests."""
    portfolio = Mock(spec=Portfolio)
    portfolio.id = "test-portfolio-123"
    portfolio.name = "Test Portfolio"
    return portfolio


@pytest.fixture
def sample_positions():
    """Positions échantillons pour les tests."""
    position1 = Mock()
    position1.symbol = "AAPL"
    position1.quantity = 10

    position2 = Mock()
    position2.symbol = "GOOGL"
    position2.quantity = 5

    return [position1, position2]


@pytest.fixture
def sample_current_prices():
    """Prix actuels échantillons."""
    return {
        "AAPL": Money(Decimal("150.00"), Currency.USD),
        "GOOGL": Money(Decimal("2800.00"), Currency.USD),
    }


@pytest.fixture
def sample_historical_prices():
    """Prix historiques échantillons."""
    return {
        "AAPL": [
            Money(Decimal("140.00"), Currency.USD),
            Money(Decimal("145.00"), Currency.USD),
            Money(Decimal("150.00"), Currency.USD),
        ],
        "GOOGL": [
            Money(Decimal("2700.00"), Currency.USD),
            Money(Decimal("2750.00"), Currency.USD),
            Money(Decimal("2800.00"), Currency.USD),
        ],
    }


class TestPerformanceAnalyzerServiceCreation:
    """Tests pour la création du service d'analyse de performance."""

    def test_should_create_performance_analyzer_service(self):
        """Test la création du service."""
        # Act
        service = PerformanceAnalyzerService()

        # Assert
        assert isinstance(service, PerformanceAnalyzerService)


class TestPerformanceAnalyzerPortfolioCalculation:
    """Tests pour les calculs de performance de portefeuille."""

    def test_should_calculate_portfolio_performance_with_default_values(
        self,
        performance_analyzer,
        sample_portfolio,
        sample_positions,
        sample_current_prices,
        sample_historical_prices,
    ):
        """Test le calcul de performance avec les valeurs par défaut."""
        # Act
        performance = performance_analyzer.calculate_portfolio_performance(
            sample_portfolio,
            sample_positions,
            sample_current_prices,
            sample_historical_prices,
        )

        # Assert
        assert isinstance(performance, PerformanceMetrics)
        assert performance.total_value.amount == Decimal("10000")
        assert abs(performance.daily_return - 0.01) < 1e-10
        assert abs(performance.monthly_return - 0.03) < 1e-10
        assert abs(performance.annual_return - 0.12) < 1e-10
        assert abs(performance.volatility - 0.05) < 1e-10
        assert abs(performance.sharpe_ratio - 1.2) < 1e-10
        assert abs(performance.max_drawdown - 0.1) < 1e-10
        assert abs(performance.beta - 1.0) < 1e-10
        assert isinstance(performance.last_updated, datetime)

    def test_should_calculate_portfolio_performance_with_benchmark(
        self,
        performance_analyzer,
        sample_portfolio,
        sample_positions,
        sample_current_prices,
        sample_historical_prices,
    ):
        """Test le calcul de performance avec benchmark."""
        # Arrange
        benchmark_returns = [0.01, 0.02, -0.01, 0.015]

        # Act
        performance = performance_analyzer.calculate_portfolio_performance(
            sample_portfolio,
            sample_positions,
            sample_current_prices,
            sample_historical_prices,
            benchmark_returns=benchmark_returns,
        )

        # Assert
        assert isinstance(performance, PerformanceMetrics)
        assert performance.total_value.amount == Decimal("10000")

    def test_should_calculate_portfolio_performance_with_custom_risk_free_rate(
        self,
        performance_analyzer,
        sample_portfolio,
        sample_positions,
        sample_current_prices,
        sample_historical_prices,
    ):
        """Test le calcul de performance avec taux sans risque personnalisé."""
        # Arrange
        risk_free_rate = 0.03

        # Act
        performance = performance_analyzer.calculate_portfolio_performance(
            sample_portfolio,
            sample_positions,
            sample_current_prices,
            sample_historical_prices,
            risk_free_rate=risk_free_rate,
        )

        # Assert
        assert isinstance(performance, PerformanceMetrics)
        assert performance.total_value.amount == Decimal("10000")


class TestPerformanceAnalyzerPositionCalculation:
    """Tests pour les calculs de performance de position."""

    def test_should_calculate_position_performance_with_current_price(
        self, performance_analyzer
    ):
        """Test le calcul de performance d'une position avec prix actuel."""
        # Arrange
        position = Mock()
        position.symbol = "AAPL"
        position.quantity = 10
        current_price = Money(Decimal("150.00"), Currency.USD)

        # Act
        performance = performance_analyzer.calculate_position_performance(
            position, current_price
        )

        # Assert
        assert isinstance(performance, dict)
        assert "unrealized_pnl" in performance
        assert "unrealized_pnl_pct" in performance
        assert "total_return" in performance
        assert "annual_return" in performance
        assert "volatility" in performance
        assert "market_value" in performance
        assert abs(performance["unrealized_pnl"] - 10.0) < 1e-10
        assert abs(performance["unrealized_pnl_pct"] - 0.1) < 1e-10
        assert abs(performance["market_value"] - 1600.0) < 1e-10

    def test_should_calculate_position_performance_with_historical_prices(
        self, performance_analyzer
    ):
        """Test le calcul de performance d'une position avec prix historiques."""
        # Arrange
        position = Mock()
        position.symbol = "AAPL"
        position.quantity = 10
        current_price = Money(Decimal("150.00"), Currency.USD)
        historical_prices = [
            Money(Decimal("140.00"), Currency.USD),
            Money(Decimal("145.00"), Currency.USD),
            Money(Decimal("150.00"), Currency.USD),
        ]

        # Act
        performance = performance_analyzer.calculate_position_performance(
            position, current_price, historical_prices
        )

        # Assert
        assert isinstance(performance, dict)
        assert abs(performance["total_return"] - 0.1) < 1e-10
        assert abs(performance["annual_return"] - 0.12) < 1e-10


class TestPerformanceAnalyzerRiskAdjustedMetrics:
    """Tests pour les métriques ajustées au risque."""

    def test_should_calculate_risk_adjusted_metrics_with_defaults(
        self, performance_analyzer
    ):
        """Test le calcul des métriques ajustées au risque avec valeurs par défaut."""
        # Arrange
        portfolio_returns = [0.01, 0.02, -0.01, 0.015]

        # Act
        metrics = performance_analyzer.calculate_risk_adjusted_metrics(
            portfolio_returns
        )

        # Assert
        assert isinstance(metrics, RiskAdjustedMetrics)
        assert abs(metrics.sharpe_ratio - 0.0) < 1e-10
        assert abs(metrics.sortino_ratio - 0.0) < 1e-10
        assert abs(metrics.calmar_ratio - 0.0) < 1e-10
        assert abs(metrics.treynor_ratio - 0.0) < 1e-10
        assert abs(metrics.jensen_alpha - 0.0) < 1e-10

    def test_should_calculate_risk_adjusted_metrics_with_benchmark(
        self, performance_analyzer
    ):
        """Test le calcul des métriques ajustées au risque avec benchmark."""
        # Arrange
        portfolio_returns = [0.01, 0.02, -0.01, 0.015]
        benchmark_returns = [0.008, 0.018, -0.012, 0.012]

        # Act
        metrics = performance_analyzer.calculate_risk_adjusted_metrics(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert isinstance(metrics, RiskAdjustedMetrics)
        assert abs(metrics.sharpe_ratio - 0.0) < 1e-10

    def test_should_calculate_risk_adjusted_metrics_with_custom_risk_free_rate(
        self, performance_analyzer
    ):
        """Test le calcul des métriques avec taux sans risque personnalisé."""
        # Arrange
        portfolio_returns = [0.01, 0.02, -0.01, 0.015]
        risk_free_rate = 0.025

        # Act
        metrics = performance_analyzer.calculate_risk_adjusted_metrics(
            portfolio_returns, risk_free_rate=risk_free_rate
        )

        # Assert
        assert isinstance(metrics, RiskAdjustedMetrics)


class TestPerformanceAnalyzerBenchmarkComparison:
    """Tests pour la comparaison avec benchmark."""

    def test_should_compare_with_benchmark_successfully(self, performance_analyzer):
        """Test la comparaison réussie avec benchmark."""
        # Arrange
        portfolio_returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        benchmark_returns = [0.008, 0.018, -0.012, 0.012, 0.003]

        # Act
        comparison = performance_analyzer.compare_with_benchmark(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert isinstance(comparison, PerformanceComparison)
        assert isinstance(comparison.portfolio_return, float)
        assert isinstance(comparison.benchmark_return, float)
        assert isinstance(comparison.alpha, float)
        assert isinstance(comparison.tracking_error, float)
        assert isinstance(comparison.information_ratio, float)

    def test_should_handle_empty_portfolio_returns(self, performance_analyzer):
        """Test la gestion des rendements de portefeuille vides."""
        # Arrange
        portfolio_returns = []
        benchmark_returns = [0.008, 0.018, -0.012]

        # Act
        comparison = performance_analyzer.compare_with_benchmark(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert abs(comparison.portfolio_return - 0.0) < 1e-10
        assert abs(comparison.benchmark_return - 0.0) < 1e-10
        assert abs(comparison.alpha - 0.0) < 1e-10
        assert abs(comparison.tracking_error - 0.0) < 1e-10
        assert abs(comparison.information_ratio - 0.0) < 1e-10

    def test_should_handle_empty_benchmark_returns(self, performance_analyzer):
        """Test la gestion des rendements de benchmark vides."""
        # Arrange
        portfolio_returns = [0.01, 0.02, -0.01]
        benchmark_returns = []

        # Act
        comparison = performance_analyzer.compare_with_benchmark(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert abs(comparison.portfolio_return - 0.0) < 1e-10
        assert abs(comparison.benchmark_return - 0.0) < 1e-10

    def test_should_handle_different_length_returns(self, performance_analyzer):
        """Test la gestion de rendements de longueurs différentes."""
        # Arrange
        portfolio_returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        benchmark_returns = [0.008, 0.018, -0.012]  # Plus court

        # Act
        comparison = performance_analyzer.compare_with_benchmark(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert isinstance(comparison, PerformanceComparison)
        # Les calculs doivent utiliser les 3 derniers éléments des deux listes


class TestPerformanceAnalyzerAttributionAnalysis:
    """Tests pour l'analyse d'attribution."""

    def test_should_calculate_attribution_analysis(
        self,
        performance_analyzer,
        sample_positions,
        sample_current_prices,
        sample_historical_prices,
    ):
        """Test le calcul d'attribution par actifs et secteurs."""
        # Arrange
        investments = Mock()

        # Act
        attribution = performance_analyzer.calculate_attribution_analysis(
            sample_positions,
            investments,
            sample_current_prices,
            sample_historical_prices,
        )

        # Assert
        assert isinstance(attribution, dict)
        assert "assets" in attribution
        assert "sectors" in attribution
        assert "AAPL" in attribution["assets"]
        assert "TECHNOLOGY" in attribution["sectors"]
        assert abs(attribution["assets"]["AAPL"]["weight"] - 1.0) < 1e-10
        assert abs(attribution["assets"]["AAPL"]["return"] - 0.1) < 1e-10
        assert abs(attribution["sectors"]["TECHNOLOGY"]["contribution"] - 0.1) < 1e-10


class TestPerformanceAnalyzerRebalancing:
    """Tests pour les suggestions de rééquilibrage."""

    def test_should_suggest_rebalancing_with_defaults(
        self,
        performance_analyzer,
        sample_portfolio,
        sample_positions,
        sample_current_prices,
    ):
        """Test les suggestions de rééquilibrage avec paramètres par défaut."""
        # Arrange
        investments = Mock()

        # Act
        suggestions = performance_analyzer.suggest_rebalancing(
            sample_portfolio, sample_positions, investments, sample_current_prices
        )

        # Assert
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0  # Implémentation stub retourne liste vide

    def test_should_suggest_rebalancing_with_target_allocation(
        self,
        performance_analyzer,
        sample_portfolio,
        sample_positions,
        sample_current_prices,
    ):
        """Test les suggestions avec allocation cible."""
        # Arrange
        investments = Mock()
        target_allocation = {"AAPL": 0.6, "GOOGL": 0.4}

        # Act
        suggestions = performance_analyzer.suggest_rebalancing(
            sample_portfolio,
            sample_positions,
            investments,
            sample_current_prices,
            target_allocation=target_allocation,
        )

        # Assert
        assert isinstance(suggestions, list)

    def test_should_suggest_rebalancing_with_custom_threshold(
        self,
        performance_analyzer,
        sample_portfolio,
        sample_positions,
        sample_current_prices,
    ):
        """Test les suggestions avec seuil de rééquilibrage personnalisé."""
        # Arrange
        investments = Mock()
        rebalance_threshold = 0.10

        # Act
        suggestions = performance_analyzer.suggest_rebalancing(
            sample_portfolio,
            sample_positions,
            investments,
            sample_current_prices,
            rebalance_threshold=rebalance_threshold,
        )

        # Assert
        assert isinstance(suggestions, list)


class TestPerformanceAnalyzerPrivateMethods:
    """Tests pour les méthodes privées du service."""

    def test_should_calculate_volatility_with_valid_returns(self, performance_analyzer):
        """Test le calcul de volatilité avec rendements valides."""
        # Arrange
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]

        # Act
        volatility = performance_analyzer._calculate_volatility(returns)

        # Assert
        assert isinstance(volatility, float)
        assert volatility > 0.0

    def test_should_calculate_volatility_with_single_return(self, performance_analyzer):
        """Test le calcul de volatilité avec un seul rendement."""
        # Arrange
        returns = [0.01]

        # Act
        volatility = performance_analyzer._calculate_volatility(returns)

        # Assert
        assert abs(volatility - 0.0) < 1e-10

    def test_should_calculate_volatility_with_empty_returns(self, performance_analyzer):
        """Test le calcul de volatilité avec liste vide."""
        # Arrange
        returns = []

        # Act
        volatility = performance_analyzer._calculate_volatility(returns)

        # Assert
        assert abs(volatility - 0.0) < 1e-10

    def test_should_calculate_sharpe_ratio_with_positive_volatility(
        self, performance_analyzer
    ):
        """Test le calcul du ratio de Sharpe avec volatilité positive."""
        # Arrange
        annual_return = 0.12
        volatility = 0.15
        risk_free_rate = 0.02

        # Act
        sharpe_ratio = performance_analyzer._calculate_sharpe_ratio(
            annual_return, volatility, risk_free_rate
        )

        # Assert
        expected_sharpe = (annual_return - risk_free_rate) / volatility
        assert sharpe_ratio == expected_sharpe
        assert sharpe_ratio > 0.0

    def test_should_calculate_sharpe_ratio_with_zero_volatility(
        self, performance_analyzer
    ):
        """Test le calcul du ratio de Sharpe avec volatilité nulle."""
        # Arrange
        annual_return = 0.12
        volatility = 0.0
        risk_free_rate = 0.02

        # Act
        sharpe_ratio = performance_analyzer._calculate_sharpe_ratio(
            annual_return, volatility, risk_free_rate
        )

        # Assert
        assert abs(sharpe_ratio - 0.0) < 1e-10

    def test_should_calculate_beta_with_valid_returns(self, performance_analyzer):
        """Test le calcul du beta avec rendements valides."""
        # Arrange
        portfolio_returns = [0.01, 0.02, -0.01, 0.015]
        benchmark_returns = [0.008, 0.018, -0.012, 0.012]

        # Act
        beta = performance_analyzer._calculate_beta(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert isinstance(beta, float)
        assert beta > 0.0

    def test_should_calculate_beta_with_empty_returns(self, performance_analyzer):
        """Test le calcul du beta avec rendements vides."""
        # Arrange
        portfolio_returns = []
        benchmark_returns = [0.008, 0.018, -0.012]

        # Act
        beta = performance_analyzer._calculate_beta(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert abs(beta - 1.0) < 1e-10

    def test_should_calculate_beta_with_insufficient_data(self, performance_analyzer):
        """Test le calcul du beta avec données insuffisantes."""
        # Arrange
        portfolio_returns = [0.01]
        benchmark_returns = [0.008]

        # Act
        beta = performance_analyzer._calculate_beta(
            portfolio_returns, benchmark_returns
        )

        # Assert
        assert abs(beta - 1.0) < 1e-10

    def test_should_calculate_cumulative_return_with_valid_returns(
        self, performance_analyzer
    ):
        """Test le calcul du rendement cumulé avec rendements valides."""
        # Arrange
        returns = [0.01, 0.02, -0.01]

        # Act
        cumulative = performance_analyzer._calculate_cumulative_return(returns)

        # Assert
        expected = (1.01 * 1.02 * 0.99) - 1.0
        assert abs(cumulative - expected) < 1e-10

    def test_should_calculate_cumulative_return_with_empty_returns(
        self, performance_analyzer
    ):
        """Test le calcul du rendement cumulé avec liste vide."""
        # Arrange
        returns = []

        # Act
        cumulative = performance_analyzer._calculate_cumulative_return(returns)

        # Assert
        assert abs(cumulative - 0.0) < 1e-10

    def test_should_calculate_daily_return_stub(
        self,
        performance_analyzer,
        sample_portfolio,
        sample_current_prices,
        sample_historical_prices,
    ):
        """Test de la méthode stub pour le calcul du rendement quotidien."""
        # Act
        daily_return = performance_analyzer._calculate_daily_return(
            sample_portfolio, sample_current_prices, sample_historical_prices
        )

        # Assert
        assert abs(daily_return - 0.0) < 1e-10

    def test_should_calculate_max_drawdown_with_delegation(self, performance_analyzer):
        """Test du calcul du drawdown maximal avec délégation."""
        # Arrange
        returns = [0.01, 0.02, -0.05, 0.03, -0.02]

        # Act
        with patch(
            "boursa_vision.domain.services.performance_analyzer.calculate_max_drawdown"
        ) as mock_calc:
            mock_calc.return_value = 0.15
            max_dd = performance_analyzer._calculate_max_drawdown(returns)

        # Assert
        mock_calc.assert_called_once_with(returns)
        assert abs(max_dd - 0.15) < 1e-10


class TestPerformanceAnalyzerEdgeCases:
    """Tests pour les cas limites du service."""

    def test_should_handle_none_portfolio(self, performance_analyzer):
        """Test la gestion d'un portefeuille None."""
        # Act
        performance = performance_analyzer.calculate_portfolio_performance(
            None, [], {}, {}
        )

        # Assert
        assert isinstance(performance, PerformanceMetrics)
        # Implémentation stub retourne toujours des métriques par défaut

    def test_should_handle_empty_positions(
        self, performance_analyzer, sample_portfolio
    ):
        """Test la gestion de positions vides."""
        # Act
        performance = performance_analyzer.calculate_portfolio_performance(
            sample_portfolio, [], {}, {}
        )

        # Assert
        assert isinstance(performance, PerformanceMetrics)

    def test_should_handle_missing_prices(
        self, performance_analyzer, sample_portfolio, sample_positions
    ):
        """Test la gestion de prix manquants."""
        # Act
        performance = performance_analyzer.calculate_portfolio_performance(
            sample_portfolio, sample_positions, {}, {}
        )

        # Assert
        assert isinstance(performance, PerformanceMetrics)


class TestPerformanceAnalyzerGetPortfolioReturns:
    """Tests pour la méthode _get_portfolio_returns."""

    def test_should_get_portfolio_returns_with_valid_prices(self, performance_analyzer):
        """Test l'obtention des rendements avec prix valides."""
        # Arrange
        historical_prices = {
            "AAPL": [
                Money(Decimal("100.00"), Currency.USD),
                Money(Decimal("105.00"), Currency.USD),
                Money(Decimal("110.00"), Currency.USD),
            ],
            "GOOGL": [
                Money(Decimal("2500.00"), Currency.USD),
                Money(Decimal("2550.00"), Currency.USD),
                Money(Decimal("2600.00"), Currency.USD),
            ],
        }

        # Act
        returns = performance_analyzer._get_portfolio_returns(historical_prices)

        # Assert
        assert isinstance(returns, list)
        assert len(returns) == 2  # Deux périodes de retour
        for ret in returns:
            assert isinstance(ret, float)

    def test_should_get_portfolio_returns_with_insufficient_prices(
        self, performance_analyzer
    ):
        """Test l'obtention des rendements avec prix insuffisants."""
        # Arrange
        historical_prices = {
            "AAPL": [Money(Decimal("100.00"), Currency.USD)]  # Un seul prix
        }

        # Act
        returns = performance_analyzer._get_portfolio_returns(historical_prices)

        # Assert
        assert returns == []

    def test_should_get_portfolio_returns_with_empty_prices(self, performance_analyzer):
        """Test l'obtention des rendements avec prix vides."""
        # Arrange
        historical_prices = {}

        # Act
        returns = performance_analyzer._get_portfolio_returns(historical_prices)

        # Assert
        assert returns == []
