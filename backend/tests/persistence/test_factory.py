from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.persistence.factory import (
    RepositoryFactoryProvider,
    RepositoryRegistry,
    SqlAlchemyRepositoryFactory,
)


class DummySession:
    pass


@pytest.mark.asyncio
async def test_sqlalchemy_repository_factory_creates_repositories(monkeypatch):
    session = DummySession()
    # Patch all SQLAlchemy repositories to MagicMock to avoid abstract class instantiation
    monkeypatch.setattr(
        "src.infrastructure.persistence.factory.SQLAlchemyUserRepository", MagicMock
    )
    monkeypatch.setattr(
        "src.infrastructure.persistence.factory.SQLAlchemyPortfolioRepository",
        MagicMock,
    )
    monkeypatch.setattr(
        "src.infrastructure.persistence.factory.SQLAlchemyMarketDataRepository",
        MagicMock,
    )
    monkeypatch.setattr(
        "src.infrastructure.persistence.factory.SQLAlchemyInvestmentRepository",
        MagicMock,
    )
    monkeypatch.setattr("src.infrastructure.persistence.factory.UnitOfWork", MagicMock)
    factory = SqlAlchemyRepositoryFactory(session)
    # Just check that the returned objects are not None
    assert factory.create_user_repository() is not None
    assert factory.create_portfolio_repository() is not None
    assert factory.create_market_data_repository() is not None
    assert factory.create_investment_repository() is not None
    assert factory.create_unit_of_work() is not None


@pytest.mark.asyncio
async def test_repository_factory_provider_get_factory(monkeypatch):
    dummy_session = DummySession()
    session_factory = MagicMock(return_value=dummy_session)
    provider = RepositoryFactoryProvider(session_factory)
    factory = await provider.get_factory()
    assert isinstance(factory, SqlAlchemyRepositoryFactory)
    factory2 = await provider.get_factory_with_session(dummy_session)
    assert isinstance(factory2, SqlAlchemyRepositoryFactory)


@pytest.mark.asyncio
async def test_repository_registry(monkeypatch):
    dummy_factory = MagicMock()
    dummy_factory.create_user_repository.return_value = "user_repo"
    dummy_factory.create_portfolio_repository.return_value = "portfolio_repo"
    dummy_factory.create_market_data_repository.return_value = "market_data_repo"
    dummy_factory.create_investment_repository.return_value = "investment_repo"
    dummy_factory.create_unit_of_work.return_value = "uow"
    provider = MagicMock()
    provider.get_factory = AsyncMock(return_value=dummy_factory)
    registry = RepositoryRegistry()
    registry.register_factory_provider(provider)
    assert await registry.get_user_repository() == "user_repo"
    assert await registry.get_portfolio_repository() == "portfolio_repo"
    assert await registry.get_market_data_repository() == "market_data_repo"
    assert await registry.get_investment_repository() == "investment_repo"
    assert await registry.get_unit_of_work() == "uow"


@pytest.mark.asyncio
async def test_registry_raises_without_provider():
    registry = RepositoryRegistry()
    with pytest.raises(RuntimeError):
        await registry.get_user_repository()
