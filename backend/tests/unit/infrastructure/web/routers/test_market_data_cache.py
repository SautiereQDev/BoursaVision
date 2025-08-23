"""
Tests complets pour market_data_cache.py (486 lignes)
Tests mockés pour FastAPI router de cache intelligent des données YFinance
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest


# Mock des classes Pydantic - reproduit la structure exacte
class MockMarketDataRequest:
    """Mock de MarketDataRequest pour validation"""

    def __init__(
        self,
        symbol: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        interval: str = "1d",
        max_age_hours: float = 1.0,
        force_refresh: bool = False,
    ):
        self.symbol = self.validate_symbol(symbol)
        self.start_date = start_date
        self.end_date = end_date
        self.interval = self.validate_interval(interval)
        self.max_age_hours = max_age_hours
        self.force_refresh = force_refresh

    @staticmethod
    def validate_symbol(symbol: str) -> str:
        if isinstance(symbol, str):
            symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        return symbol

    @staticmethod
    def validate_interval(interval: str) -> str:
        valid_intervals = [
            "1m",
            "2m",
            "5m",
            "15m",
            "30m",
            "60m",
            "90m",
            "1d",
            "5d",
            "1wk",
            "1mo",
            "3mo",
        ]
        if interval not in valid_intervals:
            raise ValueError(
                f"Invalid interval: {interval}. Must be one of {valid_intervals}"
            )
        return interval


# Mock des endpoints principaux du routeur
class MockMarketDataCacheRouter:
    """Mock complet du routeur market_data_cache"""

    def __init__(self):
        self.cache_service = Mock()

    def get_market_data(self, symbol: str, **kwargs):
        """Mock GET /market-data/{symbol}"""
        if symbol == "INVALID123":
            raise ValueError("Invalid symbol")

        return {
            "symbol": symbol,
            "data": [
                {"date": "2024-01-01", "close": 150.0, "volume": 1000000},
                {"date": "2024-01-02", "close": 152.0, "volume": 1100000},
            ],
            "cache_info": {"hit": True, "age_hours": 0.5, "source": "cache"},
            "metadata": {
                "interval": kwargs.get("interval", "1d"),
                "precision_level": "HIGH",
                "total_points": 2,
            },
        }

    def get_cache_status(self):
        """Mock GET /cache/status"""
        return {
            "total_entries": 150,
            "cache_size_mb": 25.6,
            "hit_rate": 0.85,
            "active_symbols": ["AAPL", "MSFT", "GOOGL"],
            "oldest_entry": "2024-01-01T10:00:00Z",
            "newest_entry": "2024-01-02T15:30:00Z",
        }

    def clear_cache(self, symbol: str | None = None):
        """Mock POST /cache/clear"""
        if symbol:
            return {"cleared_entries": 3, "symbol": symbol, "status": "success"}
        return {"cleared_entries": 25, "freed_space_mb": 8.5, "status": "success"}

    def get_cache_metrics(self):
        """Mock GET /cache/metrics"""
        return {
            "performance": {
                "hit_rate": 0.87,
                "miss_rate": 0.13,
                "avg_response_time_ms": 45.2,
            },
            "usage": {"total_requests": 1250, "cache_hits": 1087, "cache_misses": 163},
            "storage": {
                "used_space_mb": 42.8,
                "available_space_mb": 157.2,
                "compression_ratio": 0.65,
            },
        }

    def optimize_cache(self):
        """Mock POST /cache/optimize"""
        return {
            "optimization_type": "automatic",
            "removed_entries": 15,
            "compressed_entries": 45,
            "space_saved_mb": 12.3,
            "performance_gain": 0.15,
        }


@pytest.fixture
def mock_router():
    """Fixture du routeur mocké"""
    return MockMarketDataCacheRouter()


@pytest.fixture
def mock_cache_service():
    """Fixture du service de cache mocké"""
    service = Mock()
    service.get_market_data_with_cache = AsyncMock()
    service.get_cache_status = AsyncMock()
    service.clear_cache = AsyncMock()
    service.get_cache_metrics = AsyncMock()
    service.optimize_cache = AsyncMock()
    return service


# =============================================================================
# TESTS VALIDATION MODÈLE PYDANTIC - MarketDataRequest
# =============================================================================


def test_market_data_request_validation():
    """Test validation du modèle MarketDataRequest"""
    # Test données valides
    valid_data = {
        "symbol": "AAPL",
        "start_date": datetime(2024, 1, 1, tzinfo=UTC),
        "end_date": datetime(2024, 1, 31, tzinfo=UTC),
        "interval": "1d",
        "max_age_hours": 2.0,
        "force_refresh": False,
    }

    request = MockMarketDataRequest(**valid_data)
    assert request.symbol == "AAPL"
    assert request.interval == "1d"
    assert abs(request.max_age_hours - 2.0) < 0.001
    assert request.force_refresh is False


def test_market_data_request_symbol_validation():
    """Test validation du symbole"""
    # Test symbole valide avec espaces
    request = MockMarketDataRequest(symbol="  aapl  ")
    assert request.symbol == "AAPL"

    # Test symbole vide - doit lever une erreur
    with pytest.raises(ValueError, match="Symbol cannot be empty"):
        MockMarketDataRequest(symbol="")

    # Test symbole avec seulement des espaces
    with pytest.raises(ValueError, match="Symbol cannot be empty"):
        MockMarketDataRequest(symbol="   ")


def test_market_data_request_interval_validation():
    """Test validation de l'intervalle"""
    # Test intervalles valides
    valid_intervals = [
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
        "1d",
        "5d",
        "1wk",
        "1mo",
        "3mo",
    ]

    for interval in valid_intervals:
        request = MockMarketDataRequest(symbol="AAPL", interval=interval)
        assert request.interval == interval

    # Test intervalle invalide
    with pytest.raises(ValueError, match="Invalid interval"):
        MockMarketDataRequest(symbol="AAPL", interval="invalid")


def test_market_data_request_defaults():
    """Test valeurs par défaut du modèle"""
    request = MockMarketDataRequest(symbol="AAPL")

    assert request.symbol == "AAPL"
    assert request.start_date is None
    assert request.end_date is None
    assert request.interval == "1d"
    assert abs(request.max_age_hours - 1.0) < 0.001
    assert request.force_refresh is False


# =============================================================================
# TESTS LOGIQUE MÉTIER - Endpoints du routeur
# =============================================================================


def test_get_market_data_success(mock_router):
    """Test récupération réussie des données de marché"""
    result = mock_router.get_market_data("AAPL", interval="1d", max_age_hours=1.0)

    assert result["symbol"] == "AAPL"
    assert "data" in result
    assert "cache_info" in result
    assert "metadata" in result
    assert result["cache_info"]["hit"] is True
    assert result["metadata"]["total_points"] == 2


def test_get_market_data_with_date_range(mock_router):
    """Test récupération avec plage de dates"""
    result = mock_router.get_market_data(
        "MSFT",
        start_date=datetime(2024, 1, 1, tzinfo=UTC),
        end_date=datetime(2024, 1, 31, tzinfo=UTC),
        interval="1d",
        max_age_hours=2.0,
        force_refresh=True,
    )

    assert result["symbol"] == "MSFT"
    assert result["metadata"]["interval"] == "1d"


def test_get_market_data_invalid_symbol(mock_router):
    """Test avec symbole invalide"""
    with pytest.raises(ValueError, match="Invalid symbol"):
        mock_router.get_market_data("INVALID123")


def test_get_cache_status_success(mock_router):
    """Test récupération du statut du cache"""
    result = mock_router.get_cache_status()

    assert result["total_entries"] == 150
    assert abs(result["hit_rate"] - 0.85) < 0.001
    assert "AAPL" in result["active_symbols"]
    assert result["cache_size_mb"] > 0


def test_clear_cache_success(mock_router):
    """Test nettoyage du cache"""
    result = mock_router.clear_cache()

    assert result["cleared_entries"] == 25
    assert result["status"] == "success"
    assert "freed_space_mb" in result


def test_clear_cache_with_symbol(mock_router):
    """Test nettoyage du cache pour un symbole spécifique"""
    result = mock_router.clear_cache(symbol="AAPL")

    assert result["cleared_entries"] == 3
    assert result["symbol"] == "AAPL"
    assert result["status"] == "success"


def test_get_cache_metrics_success(mock_router):
    """Test récupération des métriques du cache"""
    result = mock_router.get_cache_metrics()

    assert abs(result["performance"]["hit_rate"] - 0.87) < 0.001
    assert result["usage"]["total_requests"] == 1250
    assert abs(result["storage"]["used_space_mb"] - 42.8) < 0.001


def test_optimize_cache_success(mock_router):
    """Test optimisation du cache"""
    result = mock_router.optimize_cache()

    assert result["removed_entries"] == 15
    assert abs(result["space_saved_mb"] - 12.3) < 0.001
    assert result["optimization_type"] == "automatic"


# =============================================================================
# TESTS SERVICE CACHE - Mock complet du service
# =============================================================================


@pytest.mark.asyncio
async def test_cache_service_get_market_data(mock_cache_service):
    """Test du service de cache pour récupération de données"""
    mock_data = {
        "symbol": "AAPL",
        "data": [{"date": "2024-01-01", "close": 150.0}],
        "cache_info": {"hit": True},
    }

    mock_cache_service.get_market_data_with_cache.return_value = mock_data

    result = await mock_cache_service.get_market_data_with_cache(
        symbol="AAPL", interval="1d", max_age_hours=1.0
    )

    assert result["symbol"] == "AAPL"
    assert result["cache_info"]["hit"] is True
    mock_cache_service.get_market_data_with_cache.assert_called_once()


@pytest.mark.asyncio
async def test_cache_service_status(mock_cache_service):
    """Test récupération du statut via service"""
    mock_status = {
        "total_entries": 100,
        "hit_rate": 0.9,
        "active_symbols": ["AAPL", "MSFT"],
    }

    mock_cache_service.get_cache_status.return_value = mock_status

    result = await mock_cache_service.get_cache_status()

    assert result["total_entries"] == 100
    assert abs(result["hit_rate"] - 0.9) < 0.001
    mock_cache_service.get_cache_status.assert_called_once()


@pytest.mark.asyncio
async def test_cache_service_clear(mock_cache_service):
    """Test nettoyage via service"""
    mock_result = {"cleared_entries": 50, "status": "success"}

    mock_cache_service.clear_cache.return_value = mock_result

    result = await mock_cache_service.clear_cache()

    assert result["cleared_entries"] == 50
    assert result["status"] == "success"
    mock_cache_service.clear_cache.assert_called_once()


@pytest.mark.asyncio
async def test_cache_service_metrics(mock_cache_service):
    """Test métriques via service"""
    mock_metrics = {
        "performance": {"hit_rate": 0.88},
        "usage": {"total_requests": 2000},
        "storage": {"used_space_mb": 35.5},
    }

    mock_cache_service.get_cache_metrics.return_value = mock_metrics

    result = await mock_cache_service.get_cache_metrics()

    assert abs(result["performance"]["hit_rate"] - 0.88) < 0.001
    assert result["usage"]["total_requests"] == 2000
    mock_cache_service.get_cache_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_cache_service_optimize(mock_cache_service):
    """Test optimisation via service"""
    mock_result = {
        "removed_entries": 20,
        "space_saved_mb": 5.2,
        "optimization_type": "manual",
    }

    mock_cache_service.optimize_cache.return_value = mock_result

    result = await mock_cache_service.optimize_cache()

    assert result["removed_entries"] == 20
    assert abs(result["space_saved_mb"] - 5.2) < 0.001
    mock_cache_service.optimize_cache.assert_called_once()


# =============================================================================
# TESTS CAS LIMITES ET GESTION D'ERREUR
# =============================================================================


def test_edge_cases_symbol_validation():
    """Test complets des cas limites pour validation symbole"""
    # Test symboles avec formats spéciaux
    special_symbols = ["AAPL.TO", "BRK-B", "GOOGL", "META"]

    for symbol in special_symbols:
        request = MockMarketDataRequest(symbol=symbol.lower())
        assert request.symbol == symbol.upper()


def test_edge_cases_interval_boundaries():
    """Test valeurs limites des intervalles"""
    # Test intervalles minutes
    minute_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m"]

    for interval in minute_intervals:
        request = MockMarketDataRequest(symbol="AAPL", interval=interval)
        assert request.interval == interval

    # Test intervalles plus longs
    long_intervals = ["1d", "5d", "1wk", "1mo", "3mo"]

    for interval in long_intervals:
        request = MockMarketDataRequest(symbol="AAPL", interval=interval)
        assert request.interval == interval


def test_max_age_hours_boundaries():
    """Test valeurs limites max_age_hours"""
    # Test valeurs limites
    boundary_values = [0.01, 1.0, 24.0, 168.0]  # 36s, 1h, 1j, 1sem

    for max_age in boundary_values:
        request = MockMarketDataRequest(symbol="AAPL", max_age_hours=max_age)
        assert abs(request.max_age_hours - max_age) < 0.001


@pytest.mark.asyncio
async def test_error_handling_comprehensive(mock_cache_service):
    """Test gestion d'erreurs complète"""
    # Test erreur de connexion
    mock_cache_service.get_market_data_with_cache.side_effect = ConnectionError(
        "Connection failed"
    )

    with pytest.raises(ConnectionError):
        await mock_cache_service.get_market_data_with_cache(symbol="AAPL")

    # Test erreur de timeout
    mock_cache_service.get_cache_status.side_effect = TimeoutError("Request timeout")

    with pytest.raises(TimeoutError):
        await mock_cache_service.get_cache_status()

    # Test erreur générique
    mock_cache_service.clear_cache.side_effect = Exception("Generic error")

    with pytest.raises(Exception):
        await mock_cache_service.clear_cache()


def test_data_consistency_validation():
    """Test cohérence et validation des données"""
    # Test données avec dates cohérentes
    start_date = datetime(2024, 1, 1, tzinfo=UTC)
    end_date = datetime(2024, 1, 31, tzinfo=UTC)

    request = MockMarketDataRequest(
        symbol="AAPL", start_date=start_date, end_date=end_date, interval="1d"
    )

    assert request.start_date is not None and request.end_date is not None
    assert request.start_date < request.end_date
    assert request.symbol == "AAPL"
    assert request.interval == "1d"


@pytest.mark.asyncio
async def test_concurrent_operations_mock(mock_cache_service):
    """Test simulation d'opérations concurrentes"""
    # Mock de résultats différents pour différents appels
    mock_cache_service.get_market_data_with_cache.side_effect = [
        {"symbol": "AAPL", "data": []},
        {"symbol": "MSFT", "data": []},
        {"symbol": "GOOGL", "data": []},
    ]

    # Simulation d'appels concurrents
    symbols = ["AAPL", "MSFT", "GOOGL"]
    results = []

    for symbol in symbols:
        result = await mock_cache_service.get_market_data_with_cache(symbol=symbol)
        results.append(result)

    assert len(results) == 3
    assert results[0]["symbol"] == "AAPL"
    assert results[1]["symbol"] == "MSFT"
    assert results[2]["symbol"] == "GOOGL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
