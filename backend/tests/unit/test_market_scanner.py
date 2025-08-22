"""
Tests unitaires pour MarketScannerService
=========================================

Tests complets pour le service de scan de marché avec toutes les stratégies,
observateurs et métriques d'analyse technique/fondamentale.
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import pandas as pd

from boursa_vision.application.services.market_scanner import (
    MarketScannerService,
    ScanStrategy,
    ScanConfig,
    ScanResult,
    ScanResultObserver,
    FullMarketStrategy,
    SectorStrategy,
    TechnicalAnalyzer,
    FundamentalAnalyzer
)

# Tolerance pour les comparaisons flottantes
FLOAT_TOLERANCE = 1e-6


@pytest.fixture
def mock_yfinance_ticker():
    """Mock YFinance ticker avec données réalistes"""
    ticker = Mock()
    
    # Mock des données d'information
    ticker.info = {
        'longName': 'Apple Inc.',
        'sector': 'Technology',
        'marketCap': 3000000000000,  # 3T
        'trailingPE': 28.5,
        'priceToBook': 45.2,
        'returnOnEquity': 0.175,
        'debtToEquity': 1.73,
        'dividendYield': 0.0045,
        'symbol': 'AAPL'
    }
    
    # Mock des données historiques
    hist_data = {
        'Close': [180.0, 182.0, 185.0, 184.0, 186.0],
        'Volume': [50000000, 55000000, 60000000, 52000000, 58000000],
        'High': [181.0, 183.0, 186.0, 185.0, 187.0],
        'Low': [179.0, 181.0, 184.0, 183.0, 185.0]
    }
    ticker.history.return_value = pd.DataFrame(hist_data)
    
    return ticker


@pytest.fixture
def market_scanner_service():
    """Instance du service MarketScanner avec mocks"""
    return MarketScannerService()


@pytest.fixture
def basic_scan_config():
    """Configuration de scan basique"""
    return ScanConfig(
        strategy=ScanStrategy.FULL_MARKET,
        max_symbols=10,
        min_market_cap=1e9,
        min_volume=100000,
        parallel_requests=5,
        timeout_per_symbol=5.0
    )


@pytest.fixture
def mock_observer():
    """Mock observer pour les résultats de scan"""
    observer = Mock(spec=ScanResultObserver)
    observer.on_scan_result = AsyncMock()
    observer.on_scan_completed = AsyncMock()
    return observer


class TestMarketScannerService:
    """Tests pour la classe MarketScannerService"""

    @pytest.mark.unit
    def test_init_scanner_service(self, market_scanner_service):
        """Test d'initialisation du service"""
        assert market_scanner_service.observers == []
        assert market_scanner_service.executor is not None
        assert hasattr(market_scanner_service, 'technical_analyzer')
        assert hasattr(market_scanner_service, 'fundamental_analyzer')

    @pytest.mark.unit
    def test_add_observer(self, market_scanner_service, mock_observer):
        """Test d'ajout d'observer"""
        market_scanner_service.add_observer(mock_observer)
        
        assert len(market_scanner_service.observers) == 1
        assert mock_observer in market_scanner_service.observers

    @pytest.mark.unit
    def test_remove_observer(self, market_scanner_service, mock_observer):
        """Test de suppression d'observer"""
        market_scanner_service.add_observer(mock_observer)
        market_scanner_service.remove_observer(mock_observer)
        
        assert len(market_scanner_service.observers) == 0
        assert mock_observer not in market_scanner_service.observers

    @pytest.mark.unit
    def test_remove_observer_not_present(self, market_scanner_service, mock_observer):
        """Test de suppression d'observer non présent"""
        # Ne devrait pas lever d'erreur
        market_scanner_service.remove_observer(mock_observer)
        assert len(market_scanner_service.observers) == 0

    @pytest.mark.unit
    def test_create_strategy_full_market(self, market_scanner_service):
        """Test de création de stratégie FULL_MARKET"""
        config = ScanConfig(strategy=ScanStrategy.FULL_MARKET)
        strategy = market_scanner_service._create_strategy(config)
        
        assert isinstance(strategy, FullMarketStrategy)

    @pytest.mark.unit
    def test_create_strategy_by_sector(self, market_scanner_service):
        """Test de création de stratégie BY_SECTOR"""
        config = ScanConfig(
            strategy=ScanStrategy.BY_SECTOR,
            sectors=["Technology", "Healthcare"]
        )
        strategy = market_scanner_service._create_strategy(config)
        
        assert isinstance(strategy, SectorStrategy)

    @pytest.mark.unit
    def test_create_strategy_default_fallback(self, market_scanner_service):
        """Test de fallback vers stratégie par défaut"""
        config = ScanConfig(strategy=ScanStrategy.BY_SECTOR)  # Sans sectors
        strategy = market_scanner_service._create_strategy(config)
        
        assert isinstance(strategy, FullMarketStrategy)

    @pytest.mark.unit
    @patch('boursa_vision.application.services.market_scanner.yf')
    async def test_notify_result(self, mock_yf, market_scanner_service, mock_observer):
        """Test de notification d'un résultat"""
        market_scanner_service.add_observer(mock_observer)
        
        result = ScanResult(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            market_cap=3e12,
            price=186.0,
            change_percent=1.08,
            volume=58000000,
            pe_ratio=28.5,
            pb_ratio=45.2,
            roe=0.175,
            debt_to_equity=1.73,
            dividend_yield=0.0045,
            rsi=65.0,
            macd_signal="BUY",
            technical_score=0.75,
            fundamental_score=0.80,
            overall_score=0.775
        )
        
        await market_scanner_service._notify_result(result)
        
        mock_observer.on_scan_result.assert_called_once_with(result)

    @pytest.mark.unit
    async def test_notify_completion(self, market_scanner_service, mock_observer):
        """Test de notification de fin de scan"""
        market_scanner_service.add_observer(mock_observer)
        
        results = [
            ScanResult(
                symbol="AAPL", name="Apple", sector="Tech", market_cap=3e12,
                price=186.0, change_percent=1.0, volume=50000000,
                pe_ratio=28.5, pb_ratio=45.2, roe=0.175, debt_to_equity=1.73,
                dividend_yield=0.0045, rsi=65.0, macd_signal="BUY",
                technical_score=0.75, fundamental_score=0.80, overall_score=0.775
            )
        ]
        
        await market_scanner_service._notify_completion(results)
        
        mock_observer.on_scan_completed.assert_called_once_with(results)

    @pytest.mark.unit
    async def test_notify_observer_error_handling(self, market_scanner_service):
        """Test de gestion d'erreur lors de notification"""
        faulty_observer = Mock(spec=ScanResultObserver)
        faulty_observer.on_scan_result = AsyncMock(side_effect=Exception("Test error"))
        
        market_scanner_service.add_observer(faulty_observer)
        
        result = ScanResult(
            symbol="TEST", name="Test", sector=None, market_cap=1e9,
            price=100.0, change_percent=0.0, volume=100000,
            pe_ratio=None, pb_ratio=None, roe=None, debt_to_equity=None,
            dividend_yield=None, rsi=None, macd_signal=None,
            technical_score=0.5, fundamental_score=0.5, overall_score=0.5
        )
        
        # Ne devrait pas lever d'erreur
        await market_scanner_service._notify_result(result)


class TestScanStrategies:
    """Tests pour les stratégies de scan"""

    @pytest.mark.unit
    async def test_full_market_strategy_get_symbols(self):
        """Test de récupération des symboles pour FullMarketStrategy"""
        strategy = FullMarketStrategy()
        config = ScanConfig(strategy=ScanStrategy.FULL_MARKET, max_symbols=50)
        
        symbols = await strategy.get_symbols_to_scan(config)
        
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert len(symbols) <= config.max_symbols
        assert all(isinstance(symbol, str) for symbol in symbols)

    @pytest.mark.unit
    def test_full_market_should_include_symbol(self):
        """Test de filtrage de symboles pour FullMarketStrategy"""
        strategy = FullMarketStrategy()
        
        # Données valides
        valid_data = {
            'marketCap': 5e9,  # 5B
            'sector': 'Technology',
            'regularMarketVolume': 1000000
        }
        assert strategy.should_include_symbol("AAPL", valid_data) is True
        
        # FullMarketStrategy inclut tout par design - même les données "invalides"
        invalid_data = {
            'marketCap': 5e8,  # 500M
            'sector': 'Technology'
        }
        # FullMarketStrategy retourne toujours True
        assert strategy.should_include_symbol("SMALL", invalid_data) is True

    @pytest.mark.unit
    async def test_sector_strategy_get_symbols(self):
        """Test de SectorStrategy avec secteurs spécifiques"""
        sectors = ["Technology", "Healthcare"]
        strategy = SectorStrategy(sectors)
        config = ScanConfig(strategy=ScanStrategy.BY_SECTOR, max_symbols=30)
        
        symbols = await strategy.get_symbols_to_scan(config)
        
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert len(symbols) <= config.max_symbols

    @pytest.mark.unit
    def test_sector_strategy_should_include_symbol(self):
        """Test de filtrage par secteur"""
        sectors = ["Technology", "Healthcare"]
        strategy = SectorStrategy(sectors)
        
        # Secteur inclus
        tech_data = {'sector': 'Technology', 'marketCap': 5e9}
        assert strategy.should_include_symbol("AAPL", tech_data) is True
        
        # Secteur non inclus
        finance_data = {'sector': 'Financial Services', 'marketCap': 5e9}
        assert strategy.should_include_symbol("JPM", finance_data) is False


class TestScanResult:
    """Tests pour la classe ScanResult"""

    @pytest.mark.unit
    def test_scan_result_creation(self):
        """Test de création d'un ScanResult"""
        result = ScanResult(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            market_cap=3e12,
            price=186.0,
            change_percent=1.08,
            volume=58000000,
            pe_ratio=28.5,
            pb_ratio=45.2,
            roe=0.175,
            debt_to_equity=1.73,
            dividend_yield=0.0045,
            rsi=65.0,
            macd_signal="BUY",
            technical_score=0.75,
            fundamental_score=0.80,
            overall_score=0.775
        )
        
        assert result.symbol == "AAPL"
        assert result.name == "Apple Inc."
        assert result.sector == "Technology"
        assert result.market_cap is not None
        assert abs(result.market_cap - 3e12) < FLOAT_TOLERANCE
        assert abs(result.price - 186.0) < FLOAT_TOLERANCE
        assert abs(result.change_percent - 1.08) < FLOAT_TOLERANCE
        assert result.volume == 58000000
        assert abs(result.technical_score - 0.75) < FLOAT_TOLERANCE
        assert abs(result.overall_score - 0.775) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_scan_result_to_dict(self):
        """Test de conversion en dictionnaire"""
        timestamp = datetime.now(timezone.utc)
        result = ScanResult(
            symbol="MSFT",
            name="Microsoft Corp.",
            sector="Technology",
            market_cap=2.5e12,
            price=420.0,
            change_percent=2.5,
            volume=25000000,
            pe_ratio=32.1,
            pb_ratio=12.5,
            roe=0.45,
            debt_to_equity=0.31,
            dividend_yield=0.0072,
            rsi=58.0,
            macd_signal="HOLD",
            technical_score=0.65,
            fundamental_score=0.85,
            overall_score=0.75,
            timestamp=timestamp
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['symbol'] == "MSFT"
        assert result_dict['name'] == "Microsoft Corp."
        assert result_dict['sector'] == "Technology"
        assert abs(result_dict['market_cap'] - 2.5e12) < FLOAT_TOLERANCE
        assert abs(result_dict['price'] - 420.0) < FLOAT_TOLERANCE
        assert result_dict['macd_signal'] == "HOLD"
        assert result_dict['timestamp'] == timestamp.isoformat()


class TestScanConfig:
    """Tests pour la classe ScanConfig"""

    @pytest.mark.unit
    def test_scan_config_defaults(self):
        """Test des valeurs par défaut de ScanConfig"""
        config = ScanConfig(strategy=ScanStrategy.FULL_MARKET)
        
        assert config.strategy == ScanStrategy.FULL_MARKET
        assert config.max_symbols == 1000
        assert abs(config.min_market_cap - 1e9) < FLOAT_TOLERANCE
        assert config.min_volume == 100000
        assert config.sectors is None
        assert len(config.exclude_symbols) == 0
        assert config.include_fundamentals is True
        assert config.include_technicals is True
        assert config.parallel_requests == 50
        assert abs(config.timeout_per_symbol - 10.0) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_scan_config_custom_values(self):
        """Test de configuration personnalisée"""
        config = ScanConfig(
            strategy=ScanStrategy.BY_SECTOR,
            max_symbols=500,
            min_market_cap=5e9,
            min_volume=500000,
            sectors=["Technology", "Healthcare"],
            exclude_symbols={"SPY", "QQQ"},
            parallel_requests=25,
            timeout_per_symbol=15.0
        )
        
        assert config.strategy == ScanStrategy.BY_SECTOR
        assert config.max_symbols == 500
        assert abs(config.min_market_cap - 5e9) < FLOAT_TOLERANCE
        assert config.min_volume == 500000
        assert config.sectors == ["Technology", "Healthcare"]
        assert "SPY" in config.exclude_symbols
        assert "QQQ" in config.exclude_symbols
        assert config.parallel_requests == 25
        assert abs(config.timeout_per_symbol - 15.0) < FLOAT_TOLERANCE


class TestMarketScanIntegration:
    """Tests d'intégration pour le scan de marché"""

    @pytest.mark.unit
    @patch('boursa_vision.application.services.market_scanner.YF_AVAILABLE', True)
    @patch('boursa_vision.application.services.market_scanner.yf')
    async def test_scan_market_full_workflow(self, mock_yf, market_scanner_service, mock_observer, basic_scan_config):
        """Test d'un workflow complet de scan"""
        # Configuration du mock YFinance
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'marketCap': 3e12,
            'trailingPE': 28.5,
            'returnOnEquity': 0.175,
        }
        
        hist_data = pd.DataFrame({
            'Close': [180.0, 182.0, 185.0],
            'Volume': [50000000, 55000000, 60000000]
        })
        mock_ticker.history.return_value = hist_data
        mock_yf.Ticker.return_value = mock_ticker
        
        # Ajout d'observer
        market_scanner_service.add_observer(mock_observer)
        
        # Mock des méthodes d'analyse (classes statiques)
        with patch('boursa_vision.application.services.market_scanner.TechnicalAnalyzer.calculate_technical_score') as mock_technical, \
             patch('boursa_vision.application.services.market_scanner.FundamentalAnalyzer.calculate_fundamental_score') as mock_fund_score, \
             patch.object(market_scanner_service, '_extract_fundamental_data') as mock_extract_fund:
            
            mock_extract_fund.return_value = {'pe_ratio': 28.5, 'pb_ratio': 2.5}
            mock_technical.return_value = 75.0
            mock_fund_score.return_value = 80.0
            
            # Configuration avec moins de symboles pour test rapide
            basic_scan_config.max_symbols = 2
            
            # Lancement du scan
            results = await market_scanner_service.scan_market(basic_scan_config)
            
            # Vérifications
            assert isinstance(results, list)
            # Vérification que les observers ont été notifiés
            assert mock_observer.on_scan_completed.called

    @pytest.mark.unit
    @patch('boursa_vision.application.services.market_scanner.YF_AVAILABLE', False)
    async def test_scan_market_yfinance_unavailable(self, market_scanner_service, basic_scan_config):
        """Test de scan quand YFinance n'est pas disponible"""
        results = await market_scanner_service.scan_market(basic_scan_config)
        
        # Devrait retourner une liste vide ou gérer l'absence de YFinance
        assert isinstance(results, list)

    @pytest.mark.unit
    async def test_scan_market_empty_symbols(self, market_scanner_service):
        """Test de scan avec liste vide de symboles"""
        with patch.object(FullMarketStrategy, 'get_symbols_to_scan', return_value=[]):
            config = ScanConfig(strategy=ScanStrategy.FULL_MARKET)
            results = await market_scanner_service.scan_market(config)
            
            assert results == []

    @pytest.mark.unit
    def test_scan_single_symbol_error_handling(self, market_scanner_service, basic_scan_config):
        """Test de gestion d'erreur pour un symbole individuel"""
        strategy = FullMarketStrategy()
        
        # Test avec YFinance non disponible
        with patch('boursa_vision.application.services.market_scanner.YF_AVAILABLE', False):
            result = market_scanner_service._scan_single_symbol("AAPL", basic_scan_config, strategy)
            assert result is None


class TestMarketScannerEdgeCases:
    """Tests des cas limites et de gestion d'erreurs"""

    @pytest.mark.unit
    def test_scan_result_with_none_values(self):
        """Test de ScanResult avec valeurs None"""
        result = ScanResult(
            symbol="UNKNOWN",
            name="Unknown Corp",
            sector=None,
            market_cap=None,
            price=50.0,
            change_percent=0.0,
            volume=0,
            pe_ratio=None,
            pb_ratio=None,
            roe=None,
            debt_to_equity=None,
            dividend_yield=None,
            rsi=None,
            macd_signal=None,
            technical_score=0.0,
            fundamental_score=0.0,
            overall_score=0.0
        )
        
        assert result.symbol == "UNKNOWN"
        assert result.sector is None
        assert result.market_cap is None
        assert abs(result.technical_score - 0.0) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_scan_config_with_empty_sectors(self):
        """Test de configuration avec liste vide de secteurs"""
        config = ScanConfig(
            strategy=ScanStrategy.BY_SECTOR,
            sectors=[]
        )
        
        assert config.sectors == []
        assert len(config.exclude_symbols) == 0

    @pytest.mark.unit
    async def test_multiple_observers_notification(self, market_scanner_service):
        """Test de notification avec plusieurs observers"""
        observer1 = Mock(spec=ScanResultObserver)
        observer1.on_scan_result = AsyncMock()
        observer1.on_scan_completed = AsyncMock()
        
        observer2 = Mock(spec=ScanResultObserver)
        observer2.on_scan_result = AsyncMock()
        observer2.on_scan_completed = AsyncMock()
        
        market_scanner_service.add_observer(observer1)
        market_scanner_service.add_observer(observer2)
        
        result = ScanResult(
            symbol="TEST", name="Test", sector=None, market_cap=1e9,
            price=100.0, change_percent=0.0, volume=100000,
            pe_ratio=None, pb_ratio=None, roe=None, debt_to_equity=None,
            dividend_yield=None, rsi=None, macd_signal=None,
            technical_score=0.5, fundamental_score=0.5, overall_score=0.5
        )
        
        await market_scanner_service._notify_result(result)
        
        observer1.on_scan_result.assert_called_once_with(result)
        observer2.on_scan_result.assert_called_once_with(result)

    @pytest.mark.unit
    def test_strategy_factory_unknown_strategy(self, market_scanner_service):
        """Test du factory avec stratégie inconnue"""
        # Créer une config avec une stratégie inconnue en mockant l'enum
        config = Mock()
        config.strategy = "UNKNOWN_STRATEGY"
        config.sectors = None
        
        strategy = market_scanner_service._create_strategy(config)
        
        # Devrait retourner la stratégie par défaut
        assert isinstance(strategy, FullMarketStrategy)


if __name__ == "__main__":
    pytest.main([__file__])
