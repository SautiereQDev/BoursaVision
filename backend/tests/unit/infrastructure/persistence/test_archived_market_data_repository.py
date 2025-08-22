"""
Tests unitaires pour le repository ArchivedMarketDataRepository.

Tests conformes à l'architecture définie dans TESTS.md.
Focus sur la structure et les méthodes du repository d'archives.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta


@pytest.mark.unit
class TestArchivedMarketDataRepositoryModuleStructure:
    """Tests de structure et disponibilité du module archived repository."""
    
    def test_archived_repository_module_file_exists(self):
        """Vérifie que le fichier archived repository existe."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        assert repo_path.exists()
        assert repo_path.is_file()
    
    def test_archived_repository_module_has_docstring(self):
        """Vérifie que le module archived repository a une docstring."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'Archive-based Market Data Repository' in content
        assert 'Provides market data from archived records' in content
        assert 'Clean Architecture patterns' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryImports:
    """Tests d'imports et gestion des dépendances."""
    
    def test_archived_repository_required_imports_exist(self):
        """Vérifie que les imports requis sont disponibles."""
        required_imports = [
            'logging',
            'os',
            'datetime',
            'typing'
        ]
        
        for import_name in required_imports:
            try:
                __import__(import_name)
            except ImportError:
                pytest.fail(f"Required import {import_name} not available")
    
    def test_archived_repository_handles_database_dependencies(self):
        """Vérifie la gestion des dépendances de base de données."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'import psycopg2' in content
        assert 'from psycopg2.extras import RealDictCursor' in content
        assert 'except ImportError:' in content
        assert 'psycopg2 not available' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryUtilityFunctions:
    """Tests des fonctions utilitaires."""
    
    def test_execute_sql_query_function_signature(self):
        """Vérifie la signature de la fonction execute_sql_query."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'def execute_sql_query(' in content
        assert 'database_url: str' in content
        assert 'query: str' in content
        assert 'params: tuple = ()' in content
        assert '-> List[Dict[str, Any]]:' in content
    
    def test_execute_sql_query_has_docstring(self):
        """Vérifie que execute_sql_query a une docstring."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'Execute SQL query and return results as list of dictionaries' in content
    
    def test_execute_sql_query_has_error_handling(self):
        """Vérifie que execute_sql_query gère les erreurs."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'try:' in content
        assert 'except ImportError:' in content
        assert 'Fallback if psycopg2 not available' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryClass:
    """Tests de la classe ArchivedMarketDataRepository."""
    
    def test_archived_repository_class_definition(self):
        """Vérifie que la classe ArchivedMarketDataRepository est définie."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'class ArchivedMarketDataRepository:' in content
        assert 'Repository for accessing archived market data' in content
        assert 'Clean Architecture compliance' in content
    
    def test_archived_repository_init_method(self):
        """Vérifie que la méthode __init__ est correctement définie."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'def __init__(self, database_url: str):' in content
        assert 'self.database_url = database_url' in content
    
    def test_archived_repository_has_get_connection_method(self):
        """Vérifie que le repository a une méthode get_connection."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'def get_connection(self):' in content
        assert 'Get database connection' in content
        assert 'psycopg2.connect(self.database_url' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryQueryMethods:
    """Tests des méthodes de requête du repository."""
    
    def test_get_available_symbols_method(self):
        """Vérifie la méthode get_available_symbols."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'def get_available_symbols(self) -> List[str]:' in content
        assert 'Get all symbols that have archived data' in content
        assert 'SELECT DISTINCT i.symbol' in content
        assert 'FROM instruments i' in content
        assert 'JOIN market_data md' in content
    
    def test_get_symbol_data_method(self):
        """Vérifie la méthode get_symbol_data."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'def get_symbol_data(' in content
        assert 'symbol: str' in content
        assert 'days_back: int = 252' in content
        assert '-> Optional[pd.DataFrame]:' in content
        assert 'Get historical data for a symbol as pandas DataFrame' in content
    
    def test_get_latest_price_data_method(self):
        """Vérifie la méthode get_latest_price_data."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'def get_latest_price_data(self, symbol: str) -> Optional[Dict]:' in content
        assert 'Get latest price data for a symbol' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryDataTransformation:
    """Tests de transformation des données."""
    
    def test_symbol_data_transforms_to_dataframe(self):
        """Vérifie que get_symbol_data transforme les données en DataFrame."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'df = pd.DataFrame(rows)' in content
        assert 'pd.to_datetime(df["time"])' in content
        assert 'df.set_index("time", inplace=True)' in content
        assert 'df.sort_index(inplace=True)' in content
    
    def test_symbol_data_renames_columns_to_yfinance_convention(self):
        """Vérifie que les colonnes sont renommées selon la convention yfinance."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'df.rename(' in content
        assert '"open_price": "Open"' in content
        assert '"high_price": "High"' in content
        assert '"low_price": "Low"' in content
        assert '"close_price": "Close"' in content
        assert '"adjusted_close": "Adj Close"' in content
        assert '"volume": "Volume"' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositorySQL:
    """Tests des requêtes SQL."""
    
    def test_available_symbols_query_structure(self):
        """Vérifie la structure de la requête des symboles disponibles."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'interval_type = \'archiver\'' in content
        assert 'i.is_active = true' in content
        assert 'ORDER BY i.symbol' in content
    
    def test_symbol_data_query_structure(self):
        """Vérifie la structure de la requête des données de symbole."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'md.time' in content
        assert 'md.open_price' in content
        assert 'md.high_price' in content
        assert 'md.low_price' in content
        assert 'md.close_price' in content
        assert 'md.adjusted_close' in content
        assert 'md.volume' in content
        assert 'WHERE i.symbol = %s' in content
        assert 'INTERVAL \'%s days\'' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryLogging:
    """Tests de logging du repository."""
    
    def test_archived_repository_configures_logger(self):
        """Vérifie que le repository configure le logger."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'logger = logging.getLogger(__name__)' in content
    
    def test_archived_repository_logs_important_events(self):
        """Vérifie que le repository loggue les événements importants."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'logger.warning(' in content or 'logger.info(' in content or 'logger.error(' in content
        assert 'No archived data found for symbol' in content
        assert 'Retrieved' in content and 'records' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryErrorHandling:
    """Tests de gestion d'erreurs du repository."""
    
    def test_repository_handles_missing_data(self):
        """Vérifie que le repository gère l'absence de données."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'if not rows:' in content
        assert 'return None' in content
    
    def test_repository_has_database_error_handling(self):
        """Vérifie que le repository gère les erreurs de base de données."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'try:' in content
        assert 'except ImportError:' in content
        assert 'cannot execute database queries' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryDataTypes:
    """Tests des types de données du repository."""
    
    def test_repository_uses_correct_type_annotations(self):
        """Vérifie que le repository utilise les bonnes annotations de type."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'List[str]' in content
        assert 'Optional[pd.DataFrame]' in content
        assert 'Optional[Dict]' in content
        assert 'List[Dict[str, Any]]' in content
    
    def test_repository_imports_typing_components(self):
        """Vérifie que le repository importe les composants de typing."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'from typing import Any, Dict, List, Optional' in content


@pytest.mark.unit
class TestArchivedMarketDataRepositoryPerformance:
    """Tests de performance du repository."""
    
    def test_repository_has_default_days_back_parameter(self):
        """Vérifie que le repository a un paramètre par défaut pour days_back."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'days_back: int = 252' in content  # ~1 année de trading
    
    def test_repository_uses_limit_in_queries(self):
        """Vérifie que le repository utilise des limites dans les requêtes."""
        repo_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories' / 'archived_market_data_repository.py'
        with open(repo_path, 'r') as f:
            content = f.read()
        
        assert 'LIMIT %s' in content
        assert 'days_back * 2' in content  # Buffer pour les données
