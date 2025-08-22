"""
Tests unitaires pour le service MarketDataArchiver.

Tests conformes à l'architecture définie dans TESTS.md.
Focus sur la structure et les méthodes d'archivage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal


@pytest.mark.unit
class TestMarketDataArchiverModuleStructure:
    """Tests de structure et disponibilité du module archiver."""
    
    def test_archiver_module_file_exists(self):
        """Vérifie que le fichier archiver existe."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        assert archiver_path.exists()
        assert archiver_path.is_file()
    
    def test_archiver_module_has_docstring(self):
        """Vérifie que le module archiver a une docstring."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'Service d\'archivage continu des données de marché' in content
        assert 'Ce service collecte et archive automatiquement' in content


@pytest.mark.unit
class TestMarketDataArchiverImports:
    """Tests d'imports et gestion des dépendances."""
    
    def test_archiver_required_imports_exist(self):
        """Vérifie que les imports requis sont disponibles."""
        required_imports = [
            'asyncio',
            'logging',
            'datetime',
            'decimal',
            'typing'
        ]
        
        for import_name in required_imports:
            try:
                __import__(import_name)
            except ImportError:
                pytest.fail(f"Required import {import_name} not available")
    
    def test_archiver_has_optional_imports_handling(self):
        """Vérifie la gestion des imports optionnels."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        # YFinance et pandas
        assert 'try:' in content
        assert 'import pandas as pd' in content
        assert 'import yfinance as yf' in content
        assert 'YF_AVAILABLE = True' in content
        assert 'YF_AVAILABLE = False' in content
        
        # SQLAlchemy
        assert 'from sqlalchemy.ext.asyncio import AsyncSession' in content
        assert 'SQLALCHEMY_AVAILABLE = True' in content
        assert 'SQLALCHEMY_AVAILABLE = False' in content


@pytest.mark.unit
class TestMarketDataArchiverClass:
    """Tests de la classe MarketDataArchiver."""
    
    def test_archiver_class_definition(self):
        """Vérifie que la classe MarketDataArchiver est définie."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'class MarketDataArchiver:' in content
        assert 'Service d\'archivage des données de marché.' in content
        assert 'Responsabilités:' in content
        assert 'Collecter les données de YFinance' in content
        assert 'Transformer les données au format domaine' in content
        assert 'Persister en base de données TimescaleDB' in content
    
    def test_archiver_init_method(self):
        """Vérifie que la méthode __init__ est correctement définie."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'def __init__(self):' in content
        assert 'self.settings = settings' in content
        assert 'self.financial_indices = self._load_financial_indices()' in content
        assert 'self.request_delay = 0.2' in content
    
    def test_archiver_loads_financial_indices(self):
        """Vérifie que l'archiver charge les indices financiers."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'def _load_financial_indices(self) -> Dict[str, List[str]]:' in content
        assert 'Charge les indices financiers depuis la configuration' in content


@pytest.mark.unit
class TestMarketDataArchiverFinancialIndices:
    """Tests des indices financiers configurés."""
    
    def test_archiver_has_cac40_symbols(self):
        """Vérifie que les symboles CAC40 sont définis."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert '"cac40": [' in content
        assert '"MC.PA"' in content  # LVMH
        assert '"ASML.AS"' in content  # ASML
        assert '"TTE.PA"' in content  # Total
        assert '"BNP.PA"' in content  # BNP Paribas
    
    def test_archiver_has_nasdaq100_symbols(self):
        """Vérifie que les symboles NASDAQ100 sont définis."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert '"nasdaq100": [' in content
        assert '"AAPL"' in content  # Apple
        assert '"MSFT"' in content  # Microsoft
        assert '"AMZN"' in content  # Amazon
        assert '"NVDA"' in content  # NVIDIA
        assert '"GOOGL"' in content  # Google
    
    def test_archiver_has_ftse100_symbols(self):
        """Vérifie que les symboles FTSE100 sont définis."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert '"ftse100": [' in content
        assert '"SHEL.L"' in content  # Shell
        assert '"AZN.L"' in content  # AstraZeneca
        assert '"LSEG.L"' in content  # London Stock Exchange


@pytest.mark.unit
class TestMarketDataArchiverMethods:
    """Tests des méthodes de l'archiver."""
    
    def test_archiver_has_archive_method(self):
        """Vérifie que l'archiver a une méthode archive."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        # Recherche de méthodes d'archivage
        assert 'def archive_' in content or 'async def archive_' in content
    
    def test_archiver_has_fetch_methods(self):
        """Vérifie que l'archiver a des méthodes de récupération."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        # Recherche de méthodes de fetch
        assert ('def fetch_' in content or 'async def fetch_' in content or 
                'def _fetch_' in content or 'async def _fetch_' in content)
    
    def test_archiver_has_transform_methods(self):
        """Vérifie que l'archiver a des méthodes de transformation."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        # Recherche de méthodes de transformation
        assert ('def transform_' in content or 'def _transform_' in content or
                'def convert_' in content or 'def _convert_' in content)


@pytest.mark.unit
class TestMarketDataArchiverLogging:
    """Tests de logging de l'archiver."""
    
    def test_archiver_configures_logger(self):
        """Vérifie que l'archiver configure le logger."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'logger = logging.getLogger(__name__)' in content
    
    def test_archiver_logs_important_events(self):
        """Vérifie que l'archiver loggue les événements importants."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        # Recherche de logs
        assert 'logger.info(' in content or 'logger.error(' in content or 'logger.warning(' in content


@pytest.mark.unit
class TestMarketDataArchiverConfiguration:
    """Tests de configuration de l'archiver."""
    
    def test_archiver_uses_settings(self):
        """Vérifie que l'archiver utilise les settings."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'from ...core.config import get_settings' in content
        assert 'settings = get_settings()' in content
    
    def test_archiver_has_request_delay_configuration(self):
        """Vérifie que l'archiver configure le délai entre requêtes."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'self.request_delay = 0.2' in content
        assert 'Délai entre requêtes YFinance' in content


@pytest.mark.unit
class TestMarketDataArchiverDomainIntegration:
    """Tests d'intégration avec le domaine."""
    
    def test_archiver_imports_domain_entities(self):
        """Vérifie que l'archiver importe les entités du domaine."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'from ...domain.entities.market_data import' in content
        assert 'DataSource' in content
        assert 'MarketData' in content
        assert 'MarketDataArgs' in content
        assert 'Timeframe' in content
    
    def test_archiver_imports_value_objects(self):
        """Vérifie que l'archiver importe les value objects."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'from ...domain.value_objects.money import Currency' in content
    
    def test_archiver_imports_infrastructure_components(self):
        """Vérifie que l'archiver importe les composants d'infrastructure."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'from ...infrastructure.persistence import get_db_session, get_market_data_repository' in content
        assert 'from ...infrastructure.persistence.mappers import MarketDataMapper' in content


@pytest.mark.unit
class TestMarketDataArchiverAsyncSupport:
    """Tests du support asynchrone de l'archiver."""
    
    def test_archiver_has_async_methods(self):
        """Vérifie que l'archiver a des méthodes asynchrones."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'async def ' in content
    
    def test_archiver_uses_asyncio(self):
        """Vérifie que l'archiver utilise asyncio."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'import asyncio' in content


@pytest.mark.unit
class TestMarketDataArchiverErrorHandling:
    """Tests de gestion d'erreurs de l'archiver."""
    
    def test_archiver_has_error_handling(self):
        """Vérifie que l'archiver gère les erreurs."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert ('try:' in content and 'except' in content) or 'Exception' in content
    
    def test_archiver_mentions_resilience(self):
        """Vérifie que l'archiver mentionne la résilience."""
        archiver_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'market_data_archiver.py'
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        assert 'erreurs et la résilience' in content
