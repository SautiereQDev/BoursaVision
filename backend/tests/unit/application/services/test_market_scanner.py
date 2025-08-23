"""
Tests for Market Scanner Service - Comprehensive Test Coverage
============================================================

Tests couvrant l'ensemble du service de scan de marché incluant :
- Stratégies de scan (Strategy Pattern)
- Analyseurs techniques et fondamentaux
- Observateurs (Observer Pattern)
- Gestion des résultats et des erreurs
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import du module à tester
from boursa_vision.application.services.market_scanner import (
    FullMarketStrategy,
    FundamentalAnalyzer,
    MarketScannerService,
    ScanConfig,
    ScanResult,
    ScanResultObserver,
    ScanStrategy,
    SectorStrategy,
    TechnicalAnalyzer,
)


@pytest.mark.unit
class TestScanResult:
    """Tests pour la classe ScanResult"""

    def test_scan_result_creation(self):
        """Test de création d'un ScanResult"""
        result = ScanResult(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            market_cap=2800000000000,
            price=150.0,
            change_percent=2.5,
            volume=50000000,
            pe_ratio=25.0,
            pb_ratio=5.2,
            roe=30.0,
            debt_to_equity=0.5,
            dividend_yield=0.8,
            rsi=55.0,
            macd_signal="BUY",
            technical_score=75.0,
            fundamental_score=80.0,
            overall_score=77.5,
        )

        assert result.symbol == "AAPL"
        assert result.name == "Apple Inc."
        assert result.sector == "Technology"
        assert result.market_cap == 2800000000000
        assert abs(result.price - 150.0) < 0.001
        assert abs(result.change_percent - 2.5) < 0.001
        assert result.volume == 50000000
        assert abs(result.pe_ratio - 25.0) < 0.001
        assert abs(result.pb_ratio - 5.2) < 0.001
        assert abs(result.roe - 30.0) < 0.001
        assert abs(result.debt_to_equity - 0.5) < 0.001
        assert abs(result.dividend_yield - 0.8) < 0.001
        assert abs(result.rsi - 55.0) < 0.001
        assert result.macd_signal == "BUY"
        assert abs(result.technical_score - 75.0) < 0.001
        assert abs(result.fundamental_score - 80.0) < 0.001
        assert abs(result.overall_score - 77.5) < 0.001
        assert isinstance(result.timestamp, datetime)

    def test_scan_result_to_dict(self):
        """Test de conversion en dictionnaire"""
        result = ScanResult(
            symbol="MSFT",
            name="Microsoft",
            sector="Technology",
            market_cap=2000000000000,
            price=300.0,
            change_percent=-1.5,
            volume=30000000,
            pe_ratio=28.0,
            pb_ratio=4.8,
            roe=25.0,
            debt_to_equity=0.3,
            dividend_yield=1.2,
            rsi=45.0,
            macd_signal="SELL",
            technical_score=40.0,
            fundamental_score=85.0,
            overall_score=67.0,
        )

        result_dict = result.to_dict()

        assert result_dict["symbol"] == "MSFT"
        assert result_dict["name"] == "Microsoft"
        assert result_dict["sector"] == "Technology"
        assert result_dict["market_cap"] == 2000000000000
        assert abs(result_dict["price"] - 300.0) < 0.001
        assert abs(result_dict["change_percent"] - (-1.5)) < 0.001
        assert result_dict["volume"] == 30000000
        assert abs(result_dict["pe_ratio"] - 28.0) < 0.001
        assert abs(result_dict["pb_ratio"] - 4.8) < 0.001
        assert abs(result_dict["roe"] - 25.0) < 0.001
        assert abs(result_dict["debt_to_equity"] - 0.3) < 0.001
        assert abs(result_dict["dividend_yield"] - 1.2) < 0.001
        assert abs(result_dict["rsi"] - 45.0) < 0.001
        assert result_dict["macd_signal"] == "SELL"
        assert abs(result_dict["technical_score"] - 40.0) < 0.001
        assert abs(result_dict["fundamental_score"] - 85.0) < 0.001
        assert abs(result_dict["overall_score"] - 67.0) < 0.001
        assert "timestamp" in result_dict

    def test_scan_result_with_none_values(self):
        """Test avec des valeurs None"""
        result = ScanResult(
            symbol="TEST",
            name="Test Company",
            sector=None,
            market_cap=None,
            price=100.0,
            change_percent=0.0,
            volume=1000000,
            pe_ratio=None,
            pb_ratio=None,
            roe=None,
            debt_to_equity=None,
            dividend_yield=None,
            rsi=None,
            macd_signal="NEUTRAL",
            technical_score=50.0,
            fundamental_score=50.0,
            overall_score=50.0,
        )

        assert result.sector is None
        assert result.market_cap is None
        assert result.pe_ratio is None
        assert result.pb_ratio is None
        assert result.roe is None
        assert result.debt_to_equity is None
        assert result.dividend_yield is None
        assert result.rsi is None


@pytest.mark.unit
class TestScanConfig:
    """Tests pour la classe ScanConfig"""

    def test_scan_config_defaults(self):
        """Test des valeurs par défaut"""
        config = ScanConfig(strategy=ScanStrategy.FULL_MARKET)

        assert config.strategy == ScanStrategy.FULL_MARKET
        assert config.max_symbols == 1000
        assert abs(config.min_market_cap - 1e9) < 0.001
        assert config.min_volume == 100000
        assert config.sectors is None
        assert config.exclude_symbols == set()
        assert config.include_fundamentals is True
        assert config.include_technicals is True
        assert config.parallel_requests == 50
        assert abs(config.timeout_per_symbol - 10.0) < 0.001

    def test_scan_config_custom_values(self):
        """Test avec des valeurs personnalisées"""
        exclude_symbols = {"TSLA", "GME"}
        sectors = ["technology", "healthcare"]

        config = ScanConfig(
            strategy=ScanStrategy.BY_SECTOR,
            max_symbols=500,
            min_market_cap=5e8,
            min_volume=50000,
            sectors=sectors,
            exclude_symbols=exclude_symbols,
            include_fundamentals=False,
            include_technicals=False,
            parallel_requests=25,
            timeout_per_symbol=5.0,
        )

        assert config.strategy == ScanStrategy.BY_SECTOR
        assert config.max_symbols == 500
        assert abs(config.min_market_cap - 5e8) < 0.001
        assert config.min_volume == 50000
        assert config.sectors == sectors
        assert config.exclude_symbols == exclude_symbols
        assert config.include_fundamentals is False
        assert config.include_technicals is False
        assert config.parallel_requests == 25
        assert abs(config.timeout_per_symbol - 5.0) < 0.001


@pytest.mark.unit
class TestScanStrategy:
    """Tests pour l'enum ScanStrategy"""

    def test_scan_strategy_values(self):
        """Test des valeurs de l'enum"""
        assert ScanStrategy.FULL_MARKET == "full_market"
        assert ScanStrategy.BY_SECTOR == "by_sector"
        assert ScanStrategy.BY_MARKET_CAP == "by_market_cap"
        assert ScanStrategy.TOP_VOLUME == "top_volume"
        assert ScanStrategy.TOP_GAINERS == "top_gainers"
        assert ScanStrategy.TOP_LOSERS == "top_losers"
        assert ScanStrategy.TECHNICAL_BREAKOUT == "technical_breakout"
        assert ScanStrategy.FUNDAMENTAL_UNDERVALUED == "fundamental_undervalued"

    def test_scan_strategy_enum_membership(self):
        """Test que toutes les stratégies sont des instances de ScanStrategy"""
        strategies = [
            ScanStrategy.FULL_MARKET,
            ScanStrategy.BY_SECTOR,
            ScanStrategy.BY_MARKET_CAP,
            ScanStrategy.TOP_VOLUME,
            ScanStrategy.TOP_GAINERS,
            ScanStrategy.TOP_LOSERS,
            ScanStrategy.TECHNICAL_BREAKOUT,
            ScanStrategy.FUNDAMENTAL_UNDERVALUED,
        ]

        for strategy in strategies:
            assert isinstance(strategy, ScanStrategy)


@pytest.mark.unit
class TestFullMarketStrategy:
    """Tests pour FullMarketStrategy"""

    @pytest.fixture
    def strategy(self):
        return FullMarketStrategy()

    @pytest.fixture
    def config(self):
        return ScanConfig(strategy=ScanStrategy.FULL_MARKET)

    def test_full_market_strategy_sector_symbols_structure(self, strategy):
        """Test de la structure des symboles par secteur"""
        assert isinstance(strategy.SECTOR_SYMBOLS, dict)
        assert "technology" in strategy.SECTOR_SYMBOLS
        assert "healthcare" in strategy.SECTOR_SYMBOLS
        assert "financial" in strategy.SECTOR_SYMBOLS
        assert "consumer_discretionary" in strategy.SECTOR_SYMBOLS
        assert "consumer_staples" in strategy.SECTOR_SYMBOLS
        assert "energy" in strategy.SECTOR_SYMBOLS
        assert "industrials" in strategy.SECTOR_SYMBOLS

        # Vérifier que chaque secteur a des symboles
        for sector, symbols in strategy.SECTOR_SYMBOLS.items():
            assert isinstance(symbols, list)
            assert len(symbols) > 0
            for symbol in symbols:
                assert isinstance(symbol, str)
                assert len(symbol) >= 1

    def test_full_market_strategy_technology_symbols(self, strategy):
        """Test des symboles technologiques"""
        tech_symbols = strategy.SECTOR_SYMBOLS["technology"]

        expected_symbols = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "GOOG",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
        ]
        for symbol in expected_symbols:
            assert symbol in tech_symbols

    def test_full_market_strategy_healthcare_symbols(self, strategy):
        """Test des symboles de santé"""
        healthcare_symbols = strategy.SECTOR_SYMBOLS["healthcare"]

        expected_symbols = ["JNJ", "PFE", "UNH", "ABBV", "TMO"]
        for symbol in expected_symbols:
            assert symbol in healthcare_symbols

    @pytest.mark.asyncio
    async def test_get_symbols_to_scan_basic(self, strategy, config):
        """Test de récupération basique des symboles"""
        symbols = await strategy.get_symbols_to_scan(config)

        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert len(symbols) <= config.max_symbols

        # Vérifier que les symboles sont des chaînes valides
        for symbol in symbols:
            assert isinstance(symbol, str)
            assert len(symbol) >= 1

    @pytest.mark.asyncio
    async def test_get_symbols_to_scan_with_exclusions(self, strategy):
        """Test avec des symboles exclus"""
        exclude_symbols = {"AAPL", "MSFT", "GOOGL"}
        config = ScanConfig(
            strategy=ScanStrategy.FULL_MARKET, exclude_symbols=exclude_symbols
        )

        symbols = await strategy.get_symbols_to_scan(config)

        # Vérifier qu'aucun symbole exclu n'est présent
        for excluded in exclude_symbols:
            assert excluded not in symbols

    @pytest.mark.asyncio
    async def test_get_symbols_to_scan_max_symbols_limit(self, strategy):
        """Test de la limite max_symbols"""
        config = ScanConfig(strategy=ScanStrategy.FULL_MARKET, max_symbols=10)

        symbols = await strategy.get_symbols_to_scan(config)

        assert len(symbols) <= 10

    def test_should_include_symbol(self, strategy):
        """Test de should_include_symbol"""
        # FullMarketStrategy inclut tous les symboles
        assert strategy.should_include_symbol("AAPL", {}) is True
        assert strategy.should_include_symbol("MSFT", {"sector": "Technology"}) is True
        assert strategy.should_include_symbol("TEST", {"invalid": "data"}) is True


@pytest.mark.unit
class TestSectorStrategy:
    """Tests pour SectorStrategy"""

    @pytest.fixture
    def strategy(self):
        return SectorStrategy(["technology", "healthcare"])

    @pytest.fixture
    def config(self):
        return ScanConfig(strategy=ScanStrategy.BY_SECTOR)

    def test_sector_strategy_initialization(self):
        """Test d'initialisation"""
        target_sectors = ["technology", "financial"]
        strategy = SectorStrategy(target_sectors)
        assert strategy.target_sectors == target_sectors

    @pytest.mark.asyncio
    async def test_get_symbols_to_scan_with_sectors(self, strategy, config):
        """Test de récupération des symboles par secteur"""
        symbols = await strategy.get_symbols_to_scan(config)

        assert isinstance(symbols, list)
        assert len(symbols) > 0

        # Doit contenir des symboles tech et healthcare
        full_strategy = FullMarketStrategy()
        expected_symbols = set()
        expected_symbols.update(full_strategy.SECTOR_SYMBOLS["technology"])
        expected_symbols.update(full_strategy.SECTOR_SYMBOLS["healthcare"])

        for symbol in symbols:
            assert symbol in expected_symbols

    @pytest.mark.asyncio
    async def test_get_symbols_to_scan_single_sector(self):
        """Test avec un seul secteur"""
        strategy = SectorStrategy(["technology"])
        config = ScanConfig(strategy=ScanStrategy.BY_SECTOR)

        symbols = await strategy.get_symbols_to_scan(config)

        full_strategy = FullMarketStrategy()
        tech_symbols = set(full_strategy.SECTOR_SYMBOLS["technology"])

        for symbol in symbols:
            assert symbol in tech_symbols

    @pytest.mark.asyncio
    async def test_get_symbols_to_scan_unknown_sector(self):
        """Test avec un secteur inconnu"""
        strategy = SectorStrategy(["unknown_sector"])
        config = ScanConfig(strategy=ScanStrategy.BY_SECTOR)

        symbols = await strategy.get_symbols_to_scan(config)

        # Devrait retourner une liste vide ou très petite
        assert isinstance(symbols, list)
        assert len(symbols) == 0

    def test_should_include_symbol_matching_sector(self, strategy):
        """Test avec secteur correspondant"""
        data = {"sector": "Technology"}
        assert strategy.should_include_symbol("AAPL", data) is True

        data = {"sector": "Healthcare"}
        assert strategy.should_include_symbol("JNJ", data) is True

    def test_should_include_symbol_non_matching_sector(self, strategy):
        """Test avec secteur non correspondant"""
        data = {"sector": "Financial Services"}
        assert strategy.should_include_symbol("JPM", data) is False

        data = {"sector": "Energy"}
        assert strategy.should_include_symbol("XOM", data) is False

    def test_should_include_symbol_empty_sector(self, strategy):
        """Test avec secteur vide"""
        data = {"sector": ""}
        assert strategy.should_include_symbol("TEST", data) is False

        data = {}
        assert strategy.should_include_symbol("TEST", data) is False


@pytest.mark.unit
class TestTechnicalAnalyzer:
    """Tests pour TechnicalAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()

    def test_calculate_rsi_with_sufficient_data(self, analyzer):
        """Test RSI avec données suffisantes"""
        # Simuler des prix avec tendance haussière
        prices = [100 + i * 0.5 for i in range(20)]

        rsi = analyzer.calculate_rsi(prices)

        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100
        # Avec une tendance haussière, RSI devrait être >= 50
        assert rsi >= 50

    def test_calculate_rsi_insufficient_data(self, analyzer):
        """Test RSI avec données insuffisantes"""
        prices = [100, 101, 102]  # Moins de 15 valeurs

        rsi = analyzer.calculate_rsi(prices)

        assert rsi == 50.0  # Valeur par défaut

    def test_calculate_rsi_empty_data(self, analyzer):
        """Test RSI avec données vides"""
        prices = []

        rsi = analyzer.calculate_rsi(prices)

        assert rsi == 50.0

    @patch("boursa_vision.application.services.market_scanner.YF_AVAILABLE", False)
    def test_calculate_rsi_yf_unavailable(self, analyzer):
        """Test RSI quand YFinance n'est pas disponible"""
        prices = [100 + i for i in range(20)]

        rsi = analyzer.calculate_rsi(prices)

        assert rsi == 50.0

    def test_calculate_macd_signal_sufficient_data(self, analyzer):
        """Test signal MACD avec données suffisantes"""
        # Simuler des prix avec crossover haussier
        prices = [100] * 10 + [100 + i * 0.1 for i in range(20)]

        signal = analyzer.calculate_macd_signal(prices)

        assert signal in ["BUY", "SELL", "NEUTRAL"]

    def test_calculate_macd_signal_insufficient_data(self, analyzer):
        """Test signal MACD avec données insuffisantes"""
        prices = [100, 101, 102]  # Moins de 26 valeurs

        signal = analyzer.calculate_macd_signal(prices)

        assert signal == "NEUTRAL"

    def test_calculate_macd_signal_empty_data(self, analyzer):
        """Test signal MACD avec données vides"""
        prices = []

        signal = analyzer.calculate_macd_signal(prices)

        assert signal == "NEUTRAL"

    @patch("boursa_vision.application.services.market_scanner.YF_AVAILABLE", False)
    def test_calculate_macd_signal_yf_unavailable(self, analyzer):
        """Test signal MACD quand YFinance n'est pas disponible"""
        prices = [100 + i for i in range(30)]

        signal = analyzer.calculate_macd_signal(prices)

        assert signal == "NEUTRAL"

    def test_calculate_technical_score_bullish_indicators(self, analyzer):
        """Test score technique avec indicateurs haussiers"""
        rsi = 65.0  # RSI dans zone favorable
        macd_signal = "BUY"
        price = 110.0
        sma_50 = 105.0
        sma_200 = 100.0  # Tendance haussière

        score = analyzer.calculate_technical_score(
            rsi, macd_signal, price, sma_50, sma_200
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 60  # Score élevé avec indicateurs haussiers

    def test_calculate_technical_score_bearish_indicators(self, analyzer):
        """Test score technique avec indicateurs baissiers"""
        rsi = 35.0  # RSI en survente
        macd_signal = "SELL"
        price = 95.0
        sma_50 = 100.0
        sma_200 = 110.0  # Tendance baissière

        score = analyzer.calculate_technical_score(
            rsi, macd_signal, price, sma_50, sma_200
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score < 50  # Score faible avec indicateurs baissiers

    def test_calculate_technical_score_neutral_indicators(self, analyzer):
        """Test score technique avec indicateurs neutres"""
        rsi = 50.0
        macd_signal = "NEUTRAL"
        price = 100.0
        sma_50 = 100.0
        sma_200 = 100.0

        score = analyzer.calculate_technical_score(
            rsi, macd_signal, price, sma_50, sma_200
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert 45 <= score <= 55  # Score autour de 50 avec indicateurs neutres

    def test_calculate_technical_score_extreme_values(self, analyzer):
        """Test avec des valeurs extrêmes"""
        # RSI très élevé
        rsi = 90.0
        macd_signal = "BUY"
        price = 200.0
        sma_50 = 150.0
        sma_200 = 100.0

        score = analyzer.calculate_technical_score(
            rsi, macd_signal, price, sma_50, sma_200
        )
        assert 0 <= score <= 100

        # RSI très bas
        rsi = 10.0
        macd_signal = "SELL"
        price = 50.0
        sma_50 = 75.0
        sma_200 = 100.0

        score = analyzer.calculate_technical_score(
            rsi, macd_signal, price, sma_50, sma_200
        )
        assert 0 <= score <= 100


@pytest.mark.unit
class TestFundamentalAnalyzer:
    """Tests pour FundamentalAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        return FundamentalAnalyzer()

    def test_score_pe_ratio_optimal_range(self, analyzer):
        """Test score P/E dans la plage optimale"""
        # P/E entre 10 et 20 est optimal
        assert abs(analyzer._score_pe_ratio(15.0) - 80.0) < 0.001
        assert abs(analyzer._score_pe_ratio(10.0) - 80.0) < 0.001
        assert abs(analyzer._score_pe_ratio(20.0) - 80.0) < 0.001

    def test_score_pe_ratio_excellent_value(self, analyzer):
        """Test score P/E avec excellente valeur"""
        assert abs(analyzer._score_pe_ratio(8.0) - 90.0) < 0.001
        assert abs(analyzer._score_pe_ratio(5.0) - 90.0) < 0.001

    def test_score_pe_ratio_acceptable_range(self, analyzer):
        """Test score P/E dans plage acceptable"""
        assert abs(analyzer._score_pe_ratio(25.0) - 60.0) < 0.001
        assert abs(analyzer._score_pe_ratio(30.0) - 60.0) < 0.001

    def test_score_pe_ratio_high_value(self, analyzer):
        """Test score P/E élevé"""
        assert abs(analyzer._score_pe_ratio(40.0) - 30.0) < 0.001
        assert abs(analyzer._score_pe_ratio(50.0) - 30.0) < 0.001

    def test_score_pe_ratio_invalid_values(self, analyzer):
        """Test score P/E avec valeurs invalides"""
        assert abs(analyzer._score_pe_ratio(None) - 50.0) < 0.001
        assert abs(analyzer._score_pe_ratio(0.0) - 50.0) < 0.001
        assert abs(analyzer._score_pe_ratio(-5.0) - 50.0) < 0.001

    def test_score_pb_ratio_excellent_value(self, analyzer):
        """Test score P/B excellent"""
        assert abs(analyzer._score_pb_ratio(0.8) - 85.0) < 0.001
        assert abs(analyzer._score_pb_ratio(0.5) - 85.0) < 0.001

    def test_score_pb_ratio_good_value(self, analyzer):
        """Test score P/B bon"""
        assert abs(analyzer._score_pb_ratio(1.5) - 65.0) < 0.001
        assert abs(analyzer._score_pb_ratio(2.0) - 65.0) < 0.001

    def test_score_pb_ratio_poor_value(self, analyzer):
        """Test score P/B faible"""
        assert abs(analyzer._score_pb_ratio(3.0) - 35.0) < 0.001
        assert abs(analyzer._score_pb_ratio(5.0) - 35.0) < 0.001

    def test_score_pb_ratio_invalid_values(self, analyzer):
        """Test score P/B avec valeurs invalides"""
        assert abs(analyzer._score_pb_ratio(None) - 50.0) < 0.001
        assert abs(analyzer._score_pb_ratio(0.0) - 50.0) < 0.001
        assert abs(analyzer._score_pb_ratio(-1.0) - 50.0) < 0.001

    def test_score_roe_excellent_value(self, analyzer):
        """Test score ROE excellent"""
        assert abs(analyzer._score_roe(25.0) - 90.0) < 0.001
        assert abs(analyzer._score_roe(30.0) - 90.0) < 0.001

    def test_score_roe_good_value(self, analyzer):
        """Test score ROE bon"""
        assert abs(analyzer._score_roe(18.0) - 75.0) < 0.001
        assert abs(analyzer._score_roe(12.0) - 60.0) < 0.001

    def test_score_roe_poor_value(self, analyzer):
        """Test score ROE faible"""
        assert abs(analyzer._score_roe(5.0) - 30.0) < 0.001
        assert abs(analyzer._score_roe(2.0) - 30.0) < 0.001

    def test_score_roe_invalid_value(self, analyzer):
        """Test score ROE avec valeur invalide"""
        assert abs(analyzer._score_roe(None) - 50.0) < 0.001

    def test_score_debt_to_equity_excellent(self, analyzer):
        """Test score Debt/Equity excellent"""
        assert abs(analyzer._score_debt_to_equity(0.2) - 85.0) < 0.001
        assert abs(analyzer._score_debt_to_equity(0.1) - 85.0) < 0.001

    def test_score_debt_to_equity_good(self, analyzer):
        """Test score Debt/Equity bon"""
        assert abs(analyzer._score_debt_to_equity(0.5) - 70.0) < 0.001
        assert abs(analyzer._score_debt_to_equity(0.8) - 45.0) < 0.001

    def test_score_debt_to_equity_poor(self, analyzer):
        """Test score Debt/Equity faible"""
        assert abs(analyzer._score_debt_to_equity(1.5) - 20.0) < 0.001
        assert abs(analyzer._score_debt_to_equity(2.0) - 20.0) < 0.001

    def test_score_debt_to_equity_invalid(self, analyzer):
        """Test score Debt/Equity invalide"""
        assert abs(analyzer._score_debt_to_equity(None) - 50.0) < 0.001

    def test_score_dividend_yield_high(self, analyzer):
        """Test score dividend yield élevé"""
        assert abs(analyzer._score_dividend_yield(4.0) - 75.0) < 0.001
        assert abs(analyzer._score_dividend_yield(5.0) - 75.0) < 0.001

    def test_score_dividend_yield_moderate(self, analyzer):
        """Test score dividend yield modéré"""
        assert abs(analyzer._score_dividend_yield(2.0) - 60.0) < 0.001
        assert abs(analyzer._score_dividend_yield(1.5) - 60.0) < 0.001

    def test_score_dividend_yield_low(self, analyzer):
        """Test score dividend yield faible"""
        assert abs(analyzer._score_dividend_yield(0.5) - 50.0) < 0.001
        assert abs(analyzer._score_dividend_yield(0.0) - 50.0) < 0.001

    def test_score_dividend_yield_invalid(self, analyzer):
        """Test score dividend yield invalide"""
        assert abs(analyzer._score_dividend_yield(None) - 50.0) < 0.001

    def test_calculate_fundamental_score_all_excellent(self, analyzer):
        """Test score fondamental avec toutes métriques excellentes"""
        score = analyzer.calculate_fundamental_score(
            pe_ratio=15.0,
            pb_ratio=0.8,
            roe=25.0,
            debt_to_equity=0.2,
            dividend_yield=4.0,
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 70  # Score élevé avec toutes bonnes métriques

    def test_calculate_fundamental_score_all_poor(self, analyzer):
        """Test score fondamental avec toutes métriques faibles"""
        score = analyzer.calculate_fundamental_score(
            pe_ratio=50.0, pb_ratio=5.0, roe=3.0, debt_to_equity=2.0, dividend_yield=0.0
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score < 50  # Score faible avec toutes mauvaises métriques

    def test_calculate_fundamental_score_mixed_metrics(self, analyzer):
        """Test score fondamental avec métriques mixtes"""
        score = analyzer.calculate_fundamental_score(
            pe_ratio=15.0,  # Bon
            pb_ratio=3.0,  # Faible
            roe=20.0,  # Excellent
            debt_to_equity=1.0,  # Moyen
            dividend_yield=2.0,  # Modéré
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert 40 <= score <= 75  # Score mitigé

    def test_calculate_fundamental_score_partial_data(self, analyzer):
        """Test score fondamental avec données partielles"""
        score = analyzer.calculate_fundamental_score(
            pe_ratio=15.0,
            pb_ratio=None,
            roe=20.0,
            debt_to_equity=None,
            dividend_yield=None,
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        # Avec peu de données, le score est plus conservateur
        assert score < 80

    def test_calculate_fundamental_score_no_data(self, analyzer):
        """Test score fondamental sans données"""
        score = analyzer.calculate_fundamental_score(
            pe_ratio=None,
            pb_ratio=None,
            roe=None,
            debt_to_equity=None,
            dividend_yield=None,
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score == 50.0  # Score par défaut


@pytest.mark.unit
class TestMarketScannerService:
    """Tests pour MarketScannerService"""

    @pytest.fixture
    def mock_yfinance_client(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_yfinance_client):
        return MarketScannerService(yfinance_client=mock_yfinance_client)

    @pytest.fixture
    def mock_observer(self):
        observer = Mock(spec=ScanResultObserver)
        observer.on_scan_result = AsyncMock()
        observer.on_scan_completed = AsyncMock()
        return observer

    def test_service_initialization(self, mock_yfinance_client):
        """Test d'initialisation du service"""
        service = MarketScannerService(yfinance_client=mock_yfinance_client)

        assert service.yfinance_client == mock_yfinance_client
        assert service.observers == []
        assert service.technical_analyzer is not None
        assert service.fundamental_analyzer is not None
        assert service.executor is not None

    def test_service_initialization_no_client(self):
        """Test d'initialisation sans client YFinance"""
        service = MarketScannerService()

        assert service.yfinance_client is None
        assert service.observers == []

    def test_add_observer(self, service, mock_observer):
        """Test d'ajout d'observer"""
        service.add_observer(mock_observer)

        assert mock_observer in service.observers
        assert len(service.observers) == 1

    def test_add_multiple_observers(self, service, mock_observer):
        """Test d'ajout de plusieurs observers"""
        observer2 = Mock(spec=ScanResultObserver)
        observer2.on_scan_result = AsyncMock()
        observer2.on_scan_completed = AsyncMock()

        service.add_observer(mock_observer)
        service.add_observer(observer2)

        assert len(service.observers) == 2
        assert mock_observer in service.observers
        assert observer2 in service.observers

    def test_remove_observer(self, service, mock_observer):
        """Test de suppression d'observer"""
        service.add_observer(mock_observer)
        service.remove_observer(mock_observer)

        assert mock_observer not in service.observers
        assert len(service.observers) == 0

    def test_remove_observer_not_present(self, service, mock_observer):
        """Test de suppression d'observer non présent"""
        # Ne devrait pas lever d'exception
        service.remove_observer(mock_observer)
        assert len(service.observers) == 0

    @pytest.mark.asyncio
    async def test_notify_result(self, service, mock_observer):
        """Test de notification de résultat"""
        service.add_observer(mock_observer)

        result = ScanResult(
            symbol="TEST",
            name="Test",
            sector=None,
            market_cap=1000000000,
            price=100.0,
            change_percent=1.0,
            volume=1000000,
            pe_ratio=None,
            pb_ratio=None,
            roe=None,
            debt_to_equity=None,
            dividend_yield=None,
            rsi=None,
            macd_signal="NEUTRAL",
            technical_score=50.0,
            fundamental_score=50.0,
            overall_score=50.0,
        )

        await service._notify_result(result)

        mock_observer.on_scan_result.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_notify_result_with_exception(self, service, mock_observer):
        """Test de notification avec exception"""
        service.add_observer(mock_observer)
        mock_observer.on_scan_result.side_effect = Exception("Test error")

        result = ScanResult(
            symbol="TEST",
            name="Test",
            sector=None,
            market_cap=1000000000,
            price=100.0,
            change_percent=1.0,
            volume=1000000,
            pe_ratio=None,
            pb_ratio=None,
            roe=None,
            debt_to_equity=None,
            dividend_yield=None,
            rsi=None,
            macd_signal="NEUTRAL",
            technical_score=50.0,
            fundamental_score=50.0,
            overall_score=50.0,
        )

        # Ne devrait pas lever d'exception
        await service._notify_result(result)

        mock_observer.on_scan_result.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_notify_completion(self, service, mock_observer):
        """Test de notification de fin"""
        service.add_observer(mock_observer)
        results = []

        await service._notify_completion(results)

        mock_observer.on_scan_completed.assert_called_once_with(results)

    def test_create_strategy_full_market(self, service):
        """Test de création de stratégie full market"""
        config = ScanConfig(strategy=ScanStrategy.FULL_MARKET)
        strategy = service._create_strategy(config)

        assert isinstance(strategy, FullMarketStrategy)

    def test_create_strategy_by_sector(self, service):
        """Test de création de stratégie par secteur"""
        config = ScanConfig(strategy=ScanStrategy.BY_SECTOR, sectors=["technology"])
        strategy = service._create_strategy(config)

        assert isinstance(strategy, SectorStrategy)
        assert strategy.target_sectors == ["technology"]

    def test_create_strategy_by_sector_no_sectors(self, service):
        """Test de création de stratégie par secteur sans secteurs spécifiés"""
        config = ScanConfig(strategy=ScanStrategy.BY_SECTOR)
        strategy = service._create_strategy(config)

        # Devrait retourner FullMarketStrategy par défaut
        assert isinstance(strategy, FullMarketStrategy)

    def test_create_strategy_unknown(self, service):
        """Test de création de stratégie inconnue"""
        config = ScanConfig(strategy=ScanStrategy.TOP_VOLUME)
        strategy = service._create_strategy(config)

        # Devrait retourner FullMarketStrategy par défaut
        assert isinstance(strategy, FullMarketStrategy)

    def test_extract_fundamental_data(self, service):
        """Test d'extraction des données fondamentales"""
        info = {
            "trailingPE": 25.0,
            "priceToBook": 3.5,
            "returnOnEquity": 0.15,  # 15%
            "debtToEquity": 0.5,
            "dividendYield": 0.02,  # 2%
        }

        data = service._extract_fundamental_data(info)

        assert data["pe_ratio"] == 25.0
        assert data["pb_ratio"] == 3.5
        assert abs(data["roe"] - 15.0) < 0.001  # Converti en pourcentage
        assert abs(data["debt_to_equity"] - 0.5) < 0.001
        assert abs(data["dividend_yield"] - 2.0) < 0.001  # Converti en pourcentage

    def test_extract_fundamental_data_missing_values(self, service):
        """Test d'extraction avec valeurs manquantes"""
        info = {
            "trailingPE": 25.0,
            # Autres valeurs manquantes
        }

        data = service._extract_fundamental_data(info)

        assert abs(data["pe_ratio"] - 25.0) < 0.001
        assert data["pb_ratio"] is None
        assert data["roe"] is None
        assert data["debt_to_equity"] is None
        assert data["dividend_yield"] is None

    def test_extract_fundamental_data_empty_info(self, service):
        """Test d'extraction avec info vide"""
        info = {}

        data = service._extract_fundamental_data(info)

        assert data["pe_ratio"] is None
        assert data["pb_ratio"] is None
        assert data["roe"] is None
        assert data["debt_to_equity"] is None
        assert data["dividend_yield"] is None

    def test_get_top_opportunities(self, service):
        """Test de récupération des meilleures opportunités"""
        results = [
            ScanResult(
                symbol="HIGH1",
                name="High1",
                sector=None,
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=85.0,
            ),
            ScanResult(
                symbol="HIGH2",
                name="High2",
                sector=None,
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=75.0,
            ),
            ScanResult(
                symbol="LOW1",
                name="Low1",
                sector=None,
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=60.0,
            ),
        ]

        opportunities = service.get_top_opportunities(results, limit=10)

        # Seuls les scores >= 70 doivent être inclus
        assert len(opportunities) == 2
        assert opportunities[0].symbol == "HIGH1"
        assert opportunities[1].symbol == "HIGH2"

    def test_get_top_opportunities_with_limit(self, service):
        """Test avec limite d'opportunités"""
        results = [
            ScanResult(
                symbol=f"HIGH{i}",
                name=f"High{i}",
                sector=None,
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=75.0,
            )
            for i in range(10)
        ]

        opportunities = service.get_top_opportunities(results, limit=5)

        assert len(opportunities) == 5

    def test_get_sector_leaders(self, service):
        """Test de récupération des leaders par secteur"""
        results = [
            ScanResult(
                symbol="TECH1",
                name="Tech1",
                sector="Technology",
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=85.0,
            ),
            ScanResult(
                symbol="TECH2",
                name="Tech2",
                sector="Technology",
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=75.0,
            ),
            ScanResult(
                symbol="HEALTH1",
                name="Health1",
                sector="Healthcare",
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=80.0,
            ),
        ]

        leaders = service.get_sector_leaders(results)

        assert "Technology" in leaders
        assert "Healthcare" in leaders
        assert len(leaders["Technology"]) == 2
        assert len(leaders["Healthcare"]) == 1
        assert leaders["Technology"][0].symbol == "TECH1"  # Plus haut score
        assert leaders["Technology"][1].symbol == "TECH2"

    def test_get_sector_leaders_empty_results(self, service):
        """Test avec résultats vides"""
        results = []

        leaders = service.get_sector_leaders(results)

        assert leaders == {}

    def test_get_sector_leaders_no_sectors(self, service):
        """Test avec résultats sans secteurs"""
        results = [
            ScanResult(
                symbol="TEST1",
                name="Test1",
                sector=None,
                market_cap=1e9,
                price=100.0,
                change_percent=1.0,
                volume=1000000,
                pe_ratio=None,
                pb_ratio=None,
                roe=None,
                debt_to_equity=None,
                dividend_yield=None,
                rsi=None,
                macd_signal="NEUTRAL",
                technical_score=50.0,
                fundamental_score=50.0,
                overall_score=75.0,
            ),
        ]

        leaders = service.get_sector_leaders(results)

        assert leaders == {}

    def test_close_service(self, service):
        """Test de fermeture du service"""
        # Ne devrait pas lever d'exception
        service.close()

        # Vérifier que l'executor est fermé
        assert service.executor._shutdown


@pytest.mark.unit
class TestMarketScannerEdgeCases:
    """Tests pour les cas limites du Market Scanner"""

    def test_scan_result_creation_with_extreme_values(self):
        """Test avec des valeurs extrêmes"""
        result = ScanResult(
            symbol="EXTREME",
            name="Extreme Corp",
            sector="Unknown",
            market_cap=999999999999999,
            price=0.001,
            change_percent=-99.99,
            volume=999999999999,
            pe_ratio=999.99,
            pb_ratio=0.001,
            roe=-50.0,
            debt_to_equity=10.0,
            dividend_yield=50.0,
            rsi=0.0,
            macd_signal="BUY",
            technical_score=0.0,
            fundamental_score=100.0,
            overall_score=50.0,
        )

        assert result.symbol == "EXTREME"
        assert result.market_cap == 999999999999999
        assert abs(result.price - 0.001) < 0.000001
        assert abs(result.change_percent - (-99.99)) < 0.001

    def test_technical_analyzer_with_extreme_rsi(self):
        """Test analyseur technique avec RSI extrême"""
        analyzer = TechnicalAnalyzer()

        score = analyzer.calculate_technical_score(
            rsi=0.0,  # RSI minimum
            macd_signal="SELL",
            price=50.0,
            sma_50=100.0,
            sma_200=150.0,
        )
        assert 0 <= score <= 100

        score = analyzer.calculate_technical_score(
            rsi=100.0,  # RSI maximum
            macd_signal="BUY",
            price=200.0,
            sma_50=150.0,
            sma_200=100.0,
        )
        assert 0 <= score <= 100

    def test_fundamental_analyzer_with_extreme_values(self):
        """Test analyseur fondamental avec valeurs extrêmes"""
        analyzer = FundamentalAnalyzer()

        score = analyzer.calculate_fundamental_score(
            pe_ratio=999.0,
            pb_ratio=50.0,
            roe=-100.0,
            debt_to_equity=20.0,
            dividend_yield=0.0,
        )
        assert 0 <= score <= 100

        score = analyzer.calculate_fundamental_score(
            pe_ratio=0.1,
            pb_ratio=0.01,
            roe=100.0,
            debt_to_equity=0.01,
            dividend_yield=20.0,
        )
        assert 0 <= score <= 100

    @patch("boursa_vision.application.services.market_scanner.YF_AVAILABLE", False)
    def test_market_scanner_without_yfinance(self):
        """Test du scanner sans YFinance disponible"""
        service = MarketScannerService()

        # Les méthodes qui dépendent de YFinance doivent gérer l'absence gracieusement
        result = service._scan_single_symbol(
            "AAPL", ScanConfig(ScanStrategy.FULL_MARKET), FullMarketStrategy()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_scan_config_edge_cases(self):
        """Test des cas limites de configuration"""
        # Configuration avec valeurs très faibles
        config = ScanConfig(
            strategy=ScanStrategy.FULL_MARKET,
            max_symbols=0,
            min_market_cap=0,
            min_volume=0,
            parallel_requests=1,
            timeout_per_symbol=0.1,
        )

        strategy = FullMarketStrategy()
        symbols = await strategy.get_symbols_to_scan(config)
        assert len(symbols) == 0  # max_symbols = 0

        # Configuration avec valeurs très élevées
        config = ScanConfig(
            strategy=ScanStrategy.FULL_MARKET,
            max_symbols=999999,
            parallel_requests=1000,
        )
        symbols = await strategy.get_symbols_to_scan(config)
        assert isinstance(symbols, list)

    def test_sector_strategy_case_insensitive(self):
        """Test que SectorStrategy gère les casses différentes"""
        strategy = SectorStrategy(["Technology", "HEALTHCARE"])

        # Test avec différentes casses
        assert strategy.should_include_symbol("AAPL", {"sector": "technology"}) is True
        assert strategy.should_include_symbol("JNJ", {"sector": "HEALTHCARE"}) is True
        assert strategy.should_include_symbol("JNJ", {"sector": "Healthcare"}) is True
        assert (
            strategy.should_include_symbol("MSFT", {"sector": "Technology Software"})
            is True
        )


class TestImportErrorHandling:
    """Tests pour gérer l'absence de yfinance/pandas"""

    def test_yfinance_unavailable_rsi(self):
        """Teste RSI quand yfinance n'est pas disponible"""
        from boursa_vision.application.services import market_scanner

        # Sauvegarder et simuler l'absence de yfinance
        original_yf = market_scanner.YF_AVAILABLE
        market_scanner.YF_AVAILABLE = False

        try:
            rsi = market_scanner.TechnicalAnalyzer.calculate_rsi([100, 101, 102])
            assert rsi == 50.0
        finally:
            market_scanner.YF_AVAILABLE = original_yf

    def test_yfinance_unavailable_macd(self):
        """Teste MACD quand yfinance n'est pas disponible"""
        from boursa_vision.application.services import market_scanner

        original_yf = market_scanner.YF_AVAILABLE
        market_scanner.YF_AVAILABLE = False

        try:
            macd = market_scanner.TechnicalAnalyzer.calculate_macd_signal(
                [100, 101, 102]
            )
            assert macd == "NEUTRAL"
        finally:
            market_scanner.YF_AVAILABLE = original_yf


class TestTechnicalScoreEdgeCases:
    """Tests pour les cas limites du score technique"""

    def test_technical_score_edge_trend_conditions(self):
        """Teste les conditions de tendance spécifiques"""
        # Test condition: price < sma_50 < sma_200
        analyzer = TechnicalAnalyzer()

        # La méthode calculate_technical_score prend (rsi, macd_signal, price, sma_50, sma_200)
        # Simuler des conditions où prix < SMA50 < SMA200 pour tester ligne 435
        score = analyzer.calculate_technical_score(
            rsi=45,  # RSI bas
            macd_signal="SELL",  # Signal bearish
            price=90,  # Prix bas
            sma_50=100,  # SMA50 supérieure au prix
            sma_200=110,  # SMA200 supérieure à SMA50
        )
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_rsi_edge_case_exactly_50(self):
        """Teste RSI retournant exactement 50"""
        # Créer des données qui donnent RSI = 50
        prices = [
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
        ]
        rsi = TechnicalAnalyzer.calculate_rsi(prices)

        # Avec des prix constants, RSI devrait être proche de 50
        assert 49 <= rsi <= 51

    def test_macd_signal_crossover_conditions(self):
        """Teste les conditions de croisement MACD"""
        # Test condition pour signal BUY (lignes 399-400)
        # Créer des prix où MACD croise au-dessus du signal
        rising_prices = [100 + i * 0.5 for i in range(30)]

        signal = TechnicalAnalyzer.calculate_macd_signal(rising_prices)
        assert signal in ["BUY", "SELL", "NEUTRAL"]
