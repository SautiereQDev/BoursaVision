"""
Fixtures pour les tests CLI.

Fournit des mocks et configurations pour tester l'interface CLI
de manière isolée.
"""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Runner Click pour tester les commandes CLI."""
    return CliRunner()


@pytest.fixture
def mock_market_data_archiver():
    """Mock du MarketDataArchiver pour les tests CLI."""
    mock_archiver = MagicMock()
    mock_archiver.archive_data = MagicMock()
    mock_archiver.get_status = MagicMock()
    mock_archiver.cleanup_old_data = MagicMock()
    return mock_archiver


@pytest.fixture
def mock_settings():
    """Mock des settings pour les tests CLI."""
    mock_settings = MagicMock()
    mock_settings.redis_url = "redis://test:6379/0"
    mock_settings.database_url = "postgresql://test"
    return mock_settings


@pytest.fixture
def mock_asyncio_run():
    """Mock de asyncio.run pour les tests CLI."""
    with patch("asyncio.run") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    """Mock du logger pour les tests CLI."""
    with patch("boursa_vision.infrastructure.background.cli.logger") as mock:
        yield mock
