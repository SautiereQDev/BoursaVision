"""
Simplified conftest.py for initial testing setup.

This provides basic fixtures for testing without complex
dependency injection until the container issues are resolved.
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add src to Python path for imports
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


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


# =====================================
# DATA FIXTURES FOR TESTING
# =====================================

@pytest.fixture
def sample_user_data():
    """Sample user data for tests."""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
    }


@pytest.fixture
def sample_portfolio_data(sample_user_data):
    """Sample portfolio data for tests."""
    return {
        "name": "Tech Portfolio",
        "description": "Technology investments portfolio for testing",
        "user_id": sample_user_data["id"],
    }


@pytest.fixture  
def sample_investment_data():
    """Sample investment data for tests."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "investment_type": "STOCK",
        "sector": "TECHNOLOGY",
        "market_cap": "LARGE",
        "exchange": "NASDAQ",
        "currency": "USD",
        "quantity": 10,
        "purchase_price": 150.0,
        "current_price": 160.0,
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for tests."""
    return {
        "symbol": "AAPL",
        "price": 160.0,
        "volume": 1000000,
        "change": 10.0,
        "change_percent": 6.67,
        "timestamp": "2024-12-01T10:00:00Z",
    }


# =====================================
# PYTEST HOOKS AND CONFIGURATION
# =====================================

def pytest_configure(config):
    """Configure pytest settings and register markers dynamically."""
    config.addinivalue_line(
        "markers", "wip: Work in progress tests (use during development)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for optimization and organization."""
    # Sort tests to run fast ones first
    items.sort(key=lambda item: "fast" not in item.keywords)
    
    # Add markers based on test location for automatic categorization
    for item in items:
        # Automatically mark tests based on file path
        test_path = str(item.fspath)
        
        if "/unit/domain/" in test_path:
            item.add_marker(pytest.mark.domain)
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.fast)
            
        elif "/unit/application/" in test_path:
            item.add_marker(pytest.mark.application)
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.fast)
            
        elif "/unit/infrastructure/" in test_path:
            item.add_marker(pytest.mark.infrastructure)
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.medium)
            
        elif "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.medium)
            
        elif "/e2e/" in test_path:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
async def reset_test_state():
    """Reset test state before each test."""
    yield
    # Cleanup happens automatically
