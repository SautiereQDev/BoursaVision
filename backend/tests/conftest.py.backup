"""
Configuration Pytest pour BoursaVision Backend
=============================================

Configuration globale des tests avec fixtures et utilitaires communs.
"""

import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import MagicMock

# Ajouter le répertoire src au sys.path pour les imports
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from faker import Faker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from httpx import AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from boursa_vision.infrastructure.web.main import create_application  # noqa: E402

# Configuration Faker pour des données cohérentes
fake = Faker("fr_FR")
Faker.seed(42)  # Pour des tests reproductibles


# ===============================
# Fixtures de base pour les tests
# ===============================


@pytest.fixture
def sample_user_data() -> dict:
    """Données utilisateur échantillon pour les tests."""
    return {
        "id": fake.uuid4(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "is_active": True,
    }


@pytest.fixture
def sample_investment_data() -> dict:
    """Données d'investissement échantillon pour les tests."""
    return {
        "id": fake.uuid4(),
        "symbol": fake.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        "name": fake.company(),
        "investment_type": "STOCK",
        "sector": "TECHNOLOGY",
        "market_cap": "LARGE",
        "exchange": "NASDAQ",
        "currency": "USD",
        "current_price": float(fake.random_number(digits=3)),
        "description": fake.text(max_nb_chars=200),
    }


# ===============================
# Fixtures pour les mocks
# ===============================


@pytest.fixture
def mock_repository() -> MagicMock:
    """Repository mocké générique."""
    mock_repo = MagicMock()
    mock_repo.save = MagicMock()
    mock_repo.find_by_id = MagicMock()
    mock_repo.find_all = MagicMock()
    mock_repo.delete = MagicMock()
    return mock_repo


# ===============================
# Fixtures d'authentification
# ===============================


class MockUser:
    """Mock user object for tests."""

    def __init__(self, user_data: dict):
        self.user_id = user_data["user_id"]
        self.email = user_data["email"]
        self.token = user_data["token"]
        self.permissions = user_data["permissions"]


@pytest.fixture
def authenticated_user() -> MockUser:
    """Utilisateur authentifié pour les tests."""
    user_data = {
        "user_id": fake.uuid4(),
        "email": fake.email(),
        "token": fake.sha256(),
        "permissions": ["read", "write", "admin"],
    }
    return MockUser(user_data)


# ===============================
# Fixtures pour les tests E2E
# ===============================


@pytest_asyncio.fixture
async def test_database_url() -> str:
    """URL de base de données de test en mémoire."""
    return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine(test_database_url):
    """Moteur de base de données de test."""
    engine = create_async_engine(test_database_url, echo=False, future=True)

    # Pour les tests E2E, on ne crée pas de tables réelles
    # Les routes API utilisent des mocks à la place

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(test_engine):
    """Factory pour les sessions de test."""
    return sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_app(test_session_factory) -> FastAPI:
    """Application FastAPI de test."""
    app = create_application()

    # Mock authentication dependencies for tests
    def mock_get_current_active_user():
        return {
            "user_id": "test-user-id",
            "id": "test-user-id",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

    # Override authentication dependency
    from boursa_vision.infrastructure.web.dependencies.auth_dependencies import (
        get_current_active_user,
    )

    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user

    return app


@pytest.fixture(autouse=True)
async def reset_mock_data():
    """Reset mock data before each test."""
    # Clear investment data
    from boursa_vision.infrastructure.web.routers.investments import _mock_investments

    _mock_investments.clear()

    # Clear portfolio data
    from boursa_vision.infrastructure.web.routers.portfolio import (
        _mock_portfolios,
        _mock_positions,
    )

    _mock_portfolios.clear()
    _mock_positions.clear()

    yield

    # Cleanup after test
    _mock_investments.clear()
    _mock_portfolios.clear()
    _mock_positions.clear()


@pytest_asyncio.fixture
async def test_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Client HTTP de test pour l'API FastAPI."""
    async with AsyncClient(app=test_app, base_url="http://testserver") as client:
        yield client
