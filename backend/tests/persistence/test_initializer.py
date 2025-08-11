import pytest

@pytest.mark.asyncio
async def test_initializer_double_initialize():
    config = PersistenceLayerConfig(database_url="sqlite+aiosqlite:///:memory:")
    initializer = PersistenceLayerInitializer(config)
    await initializer.initialize()
    # Appel double, doit juste retourner sans effet
    await initializer.initialize()

@pytest.mark.asyncio
async def test_shutdown_when_not_initialized():
    config = PersistenceLayerConfig(database_url="sqlite+aiosqlite:///:memory:")
    initializer = PersistenceLayerInitializer(config)
    # Appel direct de shutdown sans init
    await initializer.shutdown()

@pytest.mark.asyncio
async def test_setup_timescale_features_without_manager():
    config = PersistenceLayerConfig(database_url="sqlite+aiosqlite:///:memory:")
    initializer = PersistenceLayerInitializer(config)
    # Appel direct de la méthode protégée
    await initializer._setup_timescale_features()
import pytest
import asyncio
from src.infrastructure.persistence.initializer import (
    PersistenceLayerConfig,
    PersistenceLayerInitializer,
    init_persistence_layer,
    get_persistence_initializer,
    quick_setup,
    create_persistence_context,
)

@pytest.mark.asyncio
async def test_initializer_lifecycle():
    config = PersistenceLayerConfig(database_url="sqlite+aiosqlite:///:memory:", echo=False)
    initializer = PersistenceLayerInitializer(config)
    assert not initializer.is_initialized
    await initializer.initialize()
    assert initializer.is_initialized
    await initializer.shutdown()
    assert not initializer.is_initialized

@pytest.mark.asyncio
async def test_global_initializer():
    config = PersistenceLayerConfig(database_url="sqlite+aiosqlite:///:memory:")
    init = init_persistence_layer(config)
    assert get_persistence_initializer() is init

@pytest.mark.asyncio
async def test_quick_setup():
    await quick_setup("sqlite+aiosqlite:///:memory:", echo=False)
    assert get_persistence_initializer() is not None

@pytest.mark.asyncio
async def test_persistence_context():
    config = PersistenceLayerConfig(database_url="sqlite+aiosqlite:///:memory:")
    async with create_persistence_context("sqlite+aiosqlite:///:memory:") as initializer:
        assert initializer.is_initialized
    # After context exit, should be shutdown
    assert not initializer.is_initialized
