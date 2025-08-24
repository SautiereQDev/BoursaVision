"""
Progressive pytest configuration that builds DI container step by step.

This conftest.py provides fixtures for Clean Architecture testing with
pytest 8.4.1 features and progressive dependency injection integration.
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to Python path for imports
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Progressive imports - import containers individually to avoid circular dependencies
try:
    from boursa_vision.containers.core import CoreContainer
    CORE_CONTAINER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: CoreContainer not available: {e}")
    CORE_CONTAINER_AVAILABLE = False

try:
    from boursa_vision.containers.database import DatabaseContainer
    DATABASE_CONTAINER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: DatabaseContainer not available: {e}")
    DATABASE_CONTAINER_AVAILABLE = False

# Import mock services
from mocks.external_services import MockYFinanceClient, MockEmailService, MockCeleryApp


# =====================================
# SESSION SCOPE FIXTURES (Global Setup)
# =====================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Event loop fixture for the entire test session.
    
    This ensures we have a single event loop for all async tests,
    which is required for session-scoped async fixtures.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def core_container():
    """
    Core container fixture with basic configuration.
    
    This provides the foundational container for domain layer testing.
    """
    if not CORE_CONTAINER_AVAILABLE:
        pytest.skip("CoreContainer not available")
    
    container = CoreContainer()
    container.wire(modules=["tests"])
    yield container
    container.unwire()


@pytest.fixture(scope="session")
def database_container(core_container):
    """
    Database container fixture with test database configuration.
    
    This provides database access for integration tests.
    """
    if not DATABASE_CONTAINER_AVAILABLE:
        pytest.skip("DatabaseContainer not available")
    
    # Create database container manually to avoid circular dependencies
    from dependency_injector import containers, providers
    
    class TestDatabaseContainer(containers.DeclarativeContainer):
        """Test-specific database container"""
        
        # Mock database URL for tests
        database_url = providers.Configuration()
        database_url.from_value("sqlite:///:memory:")
        
        # Database engine and session factory will go here
        # For now, just provide the basic structure
    
    container = TestDatabaseContainer()
    container.wire(modules=["tests"])
    yield container
    container.unwire()


# =====================================
# FUNCTION SCOPE FIXTURES (Per Test)
# =====================================

@pytest.fixture
def mock_yfinance_client():
    """Mock YFinance client for testing external API calls."""
    return MockYFinanceClient()


@pytest.fixture
def mock_email_service():
    """Mock email service for testing notifications."""
    return MockEmailService()


@pytest.fixture
def mock_celery_app():
    """Mock Celery app for testing background tasks."""
    return MockCeleryApp()


# =====================================
# ASYNC TEST FIXTURES
# =====================================

@pytest.fixture
async def async_test_client():
    """
    Async test client for API testing.
    
    This fixture provides an async HTTP client for testing FastAPI endpoints.
    """
    # For now, return a simple mock
    # Later we'll integrate with the actual FastAPI app
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.put = AsyncMock()
    mock_client.delete = AsyncMock()
    
    yield mock_client


# =====================================
# CONFIGURATION AND UTILITIES
# =====================================

@pytest.fixture
def test_config():
    """
    Test configuration fixture.
    
    Provides configuration values for testing.
    """
    return {
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:6379/1",
        "testing": True,
        "log_level": "DEBUG",
    }


# =====================================
# PYTEST HOOKS AND PLUGINS
# =====================================

def pytest_configure(config):
    """
    Pytest configuration hook.
    
    This is called after command line parsing but before test collection.
    """
    # Configure asyncio settings
    if hasattr(config.option, 'asyncio_mode'):
        config.option.asyncio_mode = 'auto'


def pytest_collection_modifyitems(config, items):
    """
    Modify collected test items.
    
    This hook allows us to modify test items after collection,
    such as adding markers automatically based on test names or locations.
    """
    for item in items:
        # Add performance markers based on test names
        if "slow" in item.name or "e2e" in item.name:
            item.add_marker(pytest.mark.slow)
        elif "integration" in item.name:
            item.add_marker(pytest.mark.medium)
        else:
            item.add_marker(pytest.mark.fast)
        
        # Add architectural layer markers based on file path
        if "domain" in str(item.fspath):
            item.add_marker(pytest.mark.domain)
        elif "application" in str(item.fspath):
            item.add_marker(pytest.mark.application)
        elif "infrastructure" in str(item.fspath):
            item.add_marker(pytest.mark.infrastructure)
        elif "presentation" in str(item.fspath) or "web" in str(item.fspath):
            item.add_marker(pytest.mark.presentation)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Auto-use fixture that sets up the test environment for each test.
    
    This runs automatically for every test and ensures proper setup.
    """
    # Setup logic here
    yield
    # Cleanup logic here
