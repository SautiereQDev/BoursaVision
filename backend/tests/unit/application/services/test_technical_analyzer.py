"""
Tests unitaires pour TechnicalAnalyzer
=====================================

Tests unitaires complets pour le service d'analyse technique.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from boursa_vision.application.dtos import TechnicalAnalysisDTO
from boursa_vision.application.services.technical_analyzer import TechnicalAnalyzer


@pytest.fixture
def mock_investment_repository():
    """Mock repository d'investissements."""
    return AsyncMock()


@pytest.fixture
def mock_market_data_repository():
    """Mock repository de données de marché."""
    return AsyncMock()


@pytest.fixture
def mock_scoring_service():
    """Mock service de scoring."""
    return Mock()


@pytest.fixture
def technical_analyzer(
    mock_investment_repository, mock_market_data_repository, mock_scoring_service
):
    """Instance de TechnicalAnalyzer avec mocks."""
    return TechnicalAnalyzer(
        investment_repository=mock_investment_repository,
        market_data_repository=mock_market_data_repository,
        scoring_service=mock_scoring_service,
    )


@pytest.fixture
def sample_investment():
    """Investissement échantillon pour les tests."""
    return Mock(symbol="AAPL", name="Apple Inc.", investment_type="STOCK")


@pytest.fixture
def sample_market_data():
    """Données de marché échantillon."""
    market_data = Mock()
    market_data.price_data = [
        {"close": 150.0, "volume": 1000000, "date": datetime.now() - timedelta(days=i)}
        for i in range(50)
    ]
    return market_data


class TestTechnicalAnalyzerCreation:
    """Tests de création de l'analyseur technique."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_create_technical_analyzer_with_dependencies(
        self,
        mock_investment_repository,
        mock_market_data_repository,
        mock_scoring_service,
    ):
        """Test de création avec toutes les dépendances."""
        # Act
        analyzer = TechnicalAnalyzer(
            investment_repository=mock_investment_repository,
            market_data_repository=mock_market_data_repository,
            scoring_service=mock_scoring_service,
        )

        # Assert
        assert analyzer._investment_repository == mock_investment_repository
        assert analyzer._market_data_repository == mock_market_data_repository
        assert analyzer._scoring_service == mock_scoring_service


class TestTechnicalAnalyzerAnalyzeInvestment:
    """Tests d'analyse d'investissement unique."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_analyze_investment_successfully(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
        sample_market_data,
    ):
        """Test d'analyse réussie d'un investissement."""
        # Arrange
        symbol = "AAPL"
        mock_investment_repository.find_by_symbol.return_value = sample_investment
        mock_market_data_repository.get_price_history.return_value = sample_market_data

        # Act
        result = await technical_analyzer.analyze_investment(symbol)

        # Assert
        assert isinstance(result, TechnicalAnalysisDTO)
        assert result.symbol == symbol
        mock_investment_repository.find_by_symbol.assert_called_once_with(symbol)
        mock_market_data_repository.get_price_history.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_raise_error_for_nonexistent_investment(
        self, technical_analyzer, mock_investment_repository
    ):
        """Test d'erreur pour investissement inexistant."""
        # Arrange
        symbol = "NONEXISTENT"
        mock_investment_repository.find_by_symbol.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match=f"Investment with symbol {symbol} not found"
        ):
            await technical_analyzer.analyze_investment(symbol)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_raise_error_for_insufficient_market_data(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
    ):
        """Test d'erreur pour données de marché insuffisantes."""
        # Arrange
        symbol = "AAPL"
        mock_investment_repository.find_by_symbol.return_value = sample_investment
        mock_market_data_repository.get_price_history.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"Insufficient market data for {symbol}"):
            await technical_analyzer.analyze_investment(symbol)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_handle_empty_price_data(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
    ):
        """Test de gestion des données de prix vides."""
        # Arrange
        symbol = "AAPL"
        mock_investment_repository.find_by_symbol.return_value = sample_investment
        market_data = Mock()
        market_data.price_data = []
        mock_market_data_repository.get_price_history.return_value = market_data

        # Act & Assert
        with pytest.raises(ValueError, match=f"Insufficient market data for {symbol}"):
            await technical_analyzer.analyze_investment(symbol)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_use_custom_period_days(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
        sample_market_data,
    ):
        """Test d'utilisation d'une période personnalisée."""
        # Arrange
        symbol = "AAPL"
        period_days = 100
        mock_investment_repository.find_by_symbol.return_value = sample_investment
        mock_market_data_repository.get_price_history.return_value = sample_market_data

        # Act
        await technical_analyzer.analyze_investment(symbol, period_days)

        # Assert
        call_args = mock_market_data_repository.get_price_history.call_args
        assert call_args.kwargs["symbol"] == symbol
        # Vérifier que les dates correspondent à la période demandée
        start_date = call_args.kwargs["start_date"]
        end_date = call_args.kwargs["end_date"]
        actual_days = (end_date - start_date).days
        assert actual_days == period_days

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_return_empty_analysis_on_unexpected_error(
        self, technical_analyzer, mock_investment_repository
    ):
        """Test de retour d'analyse vide en cas d'erreur inattendue."""
        # Arrange
        symbol = "AAPL"
        mock_investment_repository.find_by_symbol.side_effect = Exception(
            "Unexpected error"
        )

        # Act
        result = await technical_analyzer.analyze_investment(symbol)

        # Assert
        assert isinstance(result, TechnicalAnalysisDTO)
        assert result.symbol == symbol
        assert result.rsi is None
        assert result.macd is None


class TestTechnicalAnalyzerMultipleAnalysis:
    """Tests d'analyse de multiples investissements."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_analyze_multiple_investments(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
        sample_market_data,
    ):
        """Test d'analyse de multiples investissements."""
        # Arrange
        symbols = ["AAPL", "GOOGL", "MSFT"]
        mock_investment_repository.find_by_symbol.return_value = sample_investment
        mock_market_data_repository.get_price_history.return_value = sample_market_data

        # Act
        results = await technical_analyzer.analyze_multiple_investments(symbols)

        # Assert
        assert len(results) == 3
        for symbol in symbols:
            assert symbol in results
            assert isinstance(results[symbol], TechnicalAnalysisDTO)
            assert results[symbol].symbol == symbol

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_skip_failed_analyses_in_multiple_analysis(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
        sample_market_data,
    ):
        """Test de gestion des échecs dans l'analyse multiple."""
        # Arrange
        symbols = ["AAPL", "INVALID", "GOOGL"]

        def mock_find_by_symbol(symbol):
            if symbol == "INVALID":
                return None
            return sample_investment

        mock_investment_repository.find_by_symbol.side_effect = mock_find_by_symbol
        mock_market_data_repository.get_price_history.return_value = sample_market_data

        # Act
        results = await technical_analyzer.analyze_multiple_investments(symbols)

        # Assert
        assert len(results) == 2  # Seulement AAPL et GOOGL
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "INVALID" not in results

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_handle_empty_symbols_list(self, technical_analyzer):
        """Test de gestion d'une liste de symboles vide."""
        # Act
        results = await technical_analyzer.analyze_multiple_investments([])

        # Assert
        assert results == {}


class TestTechnicalAnalyzerHelperMethods:
    """Tests des méthodes utilitaires."""

    @pytest.mark.unit
    def test_should_create_empty_analysis(self, technical_analyzer):
        """Test de création d'analyse vide."""
        # Act
        result = technical_analyzer._create_empty_analysis("AAPL")

        # Assert
        assert isinstance(result, TechnicalAnalysisDTO)
        assert result.symbol == "AAPL"
        assert result.rsi is None
        assert result.macd is None
        assert result.bollinger_position is None
        assert result.sma_20 is None
        assert result.sma_50 is None
        assert result.volume_trend is None
        assert result.support_level is None
        assert result.resistance_level is None

    @pytest.mark.unit
    def test_should_create_empty_analysis_with_default_symbol(self, technical_analyzer):
        """Test de création d'analyse vide avec symbole par défaut."""
        # Act
        result = technical_analyzer._create_empty_analysis()

        # Assert
        assert result.symbol == ""

    @pytest.mark.unit
    def test_should_calculate_technical_indicators_with_valid_data(
        self, technical_analyzer, sample_market_data
    ):
        """Test de calcul des indicateurs techniques avec données valides."""
        # Act
        indicators = technical_analyzer._calculate_technical_indicators(
            sample_market_data
        )

        # Assert
        assert isinstance(indicators, dict)
        # Les indicateurs devraient être calculés même si les valeurs exactes
        # dépendent de l'implémentation

    @pytest.mark.unit
    def test_should_return_empty_dict_for_invalid_market_data(self, technical_analyzer):
        """Test de retour de dictionnaire vide pour données invalides."""
        # Arrange
        invalid_market_data = Mock()
        invalid_market_data.price_data = None

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(
            invalid_market_data
        )

        # Assert
        assert indicators == {}

    @pytest.mark.unit
    def test_should_handle_market_data_without_price_data_attribute(
        self, technical_analyzer
    ):
        """Test de gestion des données sans attribut price_data."""
        # Arrange
        invalid_market_data = Mock(spec=[])  # Mock sans attribut price_data

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(
            invalid_market_data
        )

        # Assert
        assert indicators == {}


class TestTechnicalAnalyzerEdgeCases:
    """Tests des cas limites."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_handle_very_long_symbol(
        self, technical_analyzer, mock_investment_repository
    ):
        """Test de gestion d'un symbole très long."""
        # Arrange
        very_long_symbol = "A" * 100
        mock_investment_repository.find_by_symbol.return_value = None

        # Act & Assert
        with pytest.raises(ValueError):
            await technical_analyzer.analyze_investment(very_long_symbol)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_handle_zero_period_days(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
    ):
        """Test de gestion d'une période de 0 jours."""
        # Arrange
        symbol = "AAPL"
        mock_investment_repository.find_by_symbol.return_value = sample_investment
        mock_market_data_repository.get_price_history.return_value = None

        # Act & Assert
        with pytest.raises(ValueError):
            await technical_analyzer.analyze_investment(symbol, period_days=0)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_handle_negative_period_days(
        self,
        technical_analyzer,
        mock_investment_repository,
        mock_market_data_repository,
        sample_investment,
    ):
        """Test de gestion d'une période négative."""
        # Arrange
        symbol = "AAPL"
        mock_investment_repository.find_by_symbol.return_value = sample_investment
        mock_market_data_repository.get_price_history.return_value = None

        # Act & Assert
        with pytest.raises(ValueError):
            await technical_analyzer.analyze_investment(symbol, period_days=-10)


class TestTechnicalAnalyzerPrivateMethods:
    """Tests des méthodes privées pour améliorer la couverture."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_rsi_with_valid_data(self, technical_analyzer):
        """Test de calcul RSI avec données valides."""
        # Arrange - Prix simulant une tendance avec gains/pertes
        prices = [
            100.0,
            102.0,
            101.0,
            103.0,
            102.5,
            104.0,
            103.0,
            105.0,
            104.5,
            106.0,
            105.0,
            107.0,
            106.5,
            108.0,
            107.0,
            109.0,
        ]

        # Act
        rsi = technical_analyzer._calculate_rsi(prices, period=14)

        # Assert
        assert rsi is not None
        assert 0 <= rsi <= 100
        assert isinstance(rsi, float)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_rsi_with_insufficient_data(self, technical_analyzer):
        """Test RSI avec données insuffisantes."""
        # Arrange
        prices = [100.0, 102.0, 101.0]  # Seulement 3 prix

        # Act
        rsi = technical_analyzer._calculate_rsi(prices, period=14)

        # Assert
        assert rsi is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_rsi_with_no_losses(self, technical_analyzer):
        """Test RSI avec que des gains (pas de pertes)."""
        # Arrange - Prix uniquement croissants
        prices = [
            100.0,
            101.0,
            102.0,
            103.0,
            104.0,
            105.0,
            106.0,
            107.0,
            108.0,
            109.0,
            110.0,
            111.0,
            112.0,
            113.0,
            114.0,
        ]

        # Act
        rsi = technical_analyzer._calculate_rsi(prices, period=14)

        # Assert
        assert rsi is not None
        assert abs(rsi - 100.0) < 0.01  # RSI = 100 quand avg_loss = 0

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_rsi_with_invalid_data(self, technical_analyzer):
        """Test RSI avec données invalides."""
        # Arrange
        prices = ["invalid", None, 100.0]

        # Act
        rsi = technical_analyzer._calculate_rsi(prices, period=14)

        # Assert
        assert rsi is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_macd_with_valid_data(self, technical_analyzer):
        """Test de calcul MACD avec données valides."""
        # Arrange - 30 prix pour permettre calcul EMA 26
        prices = [100.0 + i * 0.5 for i in range(30)]

        # Act
        macd = technical_analyzer._calculate_macd(prices)

        # Assert
        assert macd is not None
        assert isinstance(macd, float)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_macd_with_insufficient_data(self, technical_analyzer):
        """Test MACD avec données insuffisantes."""
        # Arrange
        prices = [100.0, 101.0, 102.0]  # Moins de 26 prix requis

        # Act
        macd = technical_analyzer._calculate_macd(prices)

        # Assert
        assert macd is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_ema_with_valid_data(self, technical_analyzer):
        """Test de calcul EMA avec données valides."""
        # Arrange
        prices = [
            100.0,
            102.0,
            101.0,
            103.0,
            102.5,
            104.0,
            103.0,
            105.0,
            104.5,
            106.0,
            105.0,
            107.0,
            106.5,
            108.0,
        ]
        period = 12

        # Act
        ema = technical_analyzer._calculate_ema(prices, period)

        # Assert
        assert ema is not None
        assert isinstance(ema, float)
        assert ema > 0

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_ema_with_insufficient_data(self, technical_analyzer):
        """Test EMA avec données insuffisantes."""
        # Arrange
        prices = [100.0, 101.0]  # Moins que period requis
        period = 12

        # Act
        ema = technical_analyzer._calculate_ema(prices, period)

        # Assert
        assert ema is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_ema_with_invalid_data(self, technical_analyzer):
        """Test EMA avec données invalides."""
        # Arrange
        prices = [100.0, "invalid", None, 103.0]
        period = 3

        # Act
        ema = technical_analyzer._calculate_ema(prices, period)

        # Assert
        assert ema is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_sma_with_valid_data(self, technical_analyzer):
        """Test de calcul SMA avec données valides."""
        # Arrange
        prices = [100.0, 102.0, 104.0, 106.0, 108.0]
        period = 5

        # Act
        sma = technical_analyzer._calculate_sma(prices, period)

        # Assert
        assert sma is not None
        assert abs(sma - 104.0) < 0.01
        assert isinstance(sma, float)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_sma_with_insufficient_data(self, technical_analyzer):
        """Test SMA avec données insuffisantes."""
        # Arrange
        prices = [100.0, 102.0]  # Moins que period
        period = 5

        # Act
        sma = technical_analyzer._calculate_sma(prices, period)

        # Assert
        assert sma is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_sma_with_invalid_data(self, technical_analyzer):
        """Test SMA avec données invalides."""
        # Arrange
        prices = [100.0, "invalid", None]
        period = 2

        # Act
        sma = technical_analyzer._calculate_sma(prices, period)

        # Assert
        assert sma is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_bollinger_position_with_valid_data(self, technical_analyzer):
        """Test de calcul position Bollinger avec données valides."""
        # Arrange
        prices = [
            100.0,
            102.0,
            101.0,
            103.0,
            102.5,
            104.0,
            103.0,
            105.0,
            104.5,
            106.0,
            105.0,
            107.0,
            106.5,
            108.0,
            107.0,
            109.0,
            108.0,
            110.0,
            109.0,
            111.0,
            110.0,
        ]  # 21 prix

        # Act
        position = technical_analyzer._calculate_bollinger_position(prices, period=20)

        # Assert
        assert position is not None
        assert 0 <= position <= 1
        assert isinstance(position, float)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_bollinger_position_with_insufficient_data(
        self, technical_analyzer
    ):
        """Test position Bollinger avec données insuffisantes."""
        # Arrange
        prices = [100.0, 102.0, 101.0]  # Moins de 20 prix

        # Act
        position = technical_analyzer._calculate_bollinger_position(prices, period=20)

        # Assert
        assert position is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_bollinger_position_with_zero_volatility(
        self, technical_analyzer
    ):
        """Test position Bollinger avec prix identiques (volatilité nulle)."""
        # Arrange - Prix identiques = std_dev = 0
        prices = [100.0] * 25

        # Act
        position = technical_analyzer._calculate_bollinger_position(prices, period=20)

        # Assert
        assert position is not None
        assert abs(position - 0.5) < 0.01

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_bollinger_position_with_invalid_data(self, technical_analyzer):
        """Test position Bollinger avec données invalides."""
        # Arrange
        prices = [100.0, "invalid", None] + [102.0] * 18

        # Act
        position = technical_analyzer._calculate_bollinger_position(prices, period=20)

        # Assert
        assert position is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_volume_trend_with_valid_data(self, technical_analyzer):
        """Test de calcul tendance volume avec données valides."""
        # Arrange - Volume croissant puis décroissant
        volumes = [
            1000.0,
            1100.0,
            1200.0,
            1300.0,
            1400.0,
            1500.0,
            1600.0,
            1700.0,
            1800.0,
            1900.0,
            1800.0,
            1700.0,
            1600.0,
            1500.0,
            1400.0,
            1300.0,
            1200.0,
            1100.0,
            1000.0,
            900.0,
        ]

        # Act
        trend = technical_analyzer._calculate_volume_trend(volumes, period=10)

        # Assert
        assert trend is not None
        assert isinstance(trend, float)
        # Tendance devrait être négative (volume récent < volume ancien)
        assert trend < 0

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_volume_trend_with_insufficient_data(self, technical_analyzer):
        """Test tendance volume avec données insuffisantes."""
        # Arrange
        volumes = [1000.0, 1100.0, 1200.0]  # Moins de period*2

        # Act
        trend = technical_analyzer._calculate_volume_trend(volumes, period=10)

        # Assert
        assert trend is None

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_volume_trend_with_zero_older_average(self, technical_analyzer):
        """Test tendance volume avec moyenne ancienne nulle."""
        # Arrange - Volumes anciens à zéro
        volumes = [0.0] * 10 + [1000.0] * 10

        # Act
        trend = technical_analyzer._calculate_volume_trend(volumes, period=10)

        # Assert
        assert trend is not None
        assert abs(trend - 0.0) < 0.01

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_volume_trend_with_invalid_data(self, technical_analyzer):
        """Test tendance volume avec données invalides."""
        # Arrange
        volumes = [1000.0, "invalid", None] + [1100.0] * 17

        # Act
        trend = technical_analyzer._calculate_volume_trend(volumes, period=10)

        # Assert
        assert trend is None


class TestTechnicalAnalyzerCalculateTechnicalIndicators:
    """Tests pour la méthode _calculate_technical_indicators."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_valid_market_data(
        self, technical_analyzer
    ):
        """Test de calcul des indicateurs avec données de marché valides."""
        # Arrange
        market_data = Mock()
        price_points = []
        for i in range(30):
            price_point = Mock()
            price_point.close = 100.0 + i
            price_point.volume = 1000000 + i * 10000
            price_points.append(price_point)
        market_data.price_data = price_points

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert isinstance(indicators, dict)
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "bollinger_position" in indicators
        assert "sma_20" in indicators
        assert "sma_50" in indicators
        assert "volume_trend" in indicators
        assert "support_level" in indicators
        assert "resistance_level" in indicators

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_insufficient_data(
        self, technical_analyzer
    ):
        """Test avec données insuffisantes (moins de 14 points)."""
        # Arrange
        market_data = Mock()
        price_points = []
        for i in range(10):  # Seulement 10 points
            price_point = Mock()
            price_point.close = 100.0 + i
            price_point.volume = 1000000
            price_points.append(price_point)
        market_data.price_data = price_points

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert indicators == {}

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_no_price_data(
        self, technical_analyzer
    ):
        """Test avec market_data sans price_data."""
        # Arrange
        market_data = Mock()
        market_data.price_data = None

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert indicators == {}

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_invalid_price_entries(
        self, technical_analyzer
    ):
        """Test avec entrées de prix invalides."""
        # Arrange
        market_data = Mock()
        price_points = []

        # Quelques points valides au début
        for _i in range(3):
            price_point = Mock()
            price_point.close = 100.0
            price_point.volume = 1000000
            price_points.append(price_point)

        # Points invalides
        invalid_point1 = Mock()
        invalid_point1.close = "invalid"
        invalid_point1.volume = 1000000
        price_points.append(invalid_point1)

        invalid_point2 = Mock()
        invalid_point2.close = None
        invalid_point2.volume = 1000000
        price_points.append(invalid_point2)

        # Plus de points valides pour avoir 15+ points au total
        for i in range(15):
            price_point = Mock()
            price_point.close = 100.0 + i
            price_point.volume = 1000000
            price_points.append(price_point)

        market_data.price_data = price_points

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert isinstance(indicators, dict)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_missing_close_key(
        self, technical_analyzer
    ):
        """Test avec des entrées manquant l'attribut 'close'."""
        # Arrange
        market_data = Mock()
        price_points = []
        for _ in range(20):
            price_point = Mock()
            price_point.volume = 1000000  # Pas d'attribut close
            price_points.append(price_point)
        market_data.price_data = price_points

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert indicators == {}

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_missing_volume_key(
        self, technical_analyzer
    ):
        """Test avec des entrées manquant l'attribut 'volume'."""
        # Arrange
        market_data = Mock()
        price_points = []
        for i in range(20):
            price_point = Mock()
            price_point.close = 100.0 + i  # Pas d'attribut volume
            price_points.append(price_point)
        market_data.price_data = price_points

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert indicators == {}

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_support_resistance_levels(
        self, technical_analyzer
    ):
        """Test de calcul des niveaux de support et résistance."""
        # Arrange
        market_data = Mock()
        price_points = []
        for i in range(25):
            price_point = Mock()
            price_point.close = 95.0 + (i % 10)  # Prix oscillants
            price_point.volume = 1000000
            price_points.append(price_point)
        market_data.price_data = price_points

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert indicators["support_level"] is not None
        assert indicators["resistance_level"] is not None
        assert indicators["support_level"] <= indicators["resistance_level"]

    @pytest.mark.unit
    @pytest.mark.fast
    def test_calculate_technical_indicators_with_exception_handling(
        self, technical_analyzer
    ):
        """Test de gestion des exceptions."""
        # Arrange
        market_data = Mock()
        market_data.price_data = "not_a_list"

        # Act
        indicators = technical_analyzer._calculate_technical_indicators(market_data)

        # Assert
        assert indicators == {}
