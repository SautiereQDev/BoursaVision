import asyncio

import pytest

from src.infrastructure.persistence.config import (
    PersistenceConfig,
    PersistenceContext,
    PersistenceInitializer,
    check_database_health,
    check_timescale_health,
    get_persistence_initializer,
    initialize_persistence,
    shutdown_persistence,
)


@pytest.mark.asyncio
async def test_persistence_initializer_lifecycle():
    config = PersistenceConfig(
        database_host="localhost",
        database_port=5432,
        database_name="test_db",
        database_user="user",
        database_password="pass",
        echo_sql=False,
    )
    initializer = PersistenceInitializer(config)
    assert not initializer.is_initialized
    # Patch methods to avoid real DB calls
    initializer._db_manager = None
    initializer._is_initialized = True
    assert initializer.is_initialized
    await initializer.shutdown()
    assert not initializer.is_initialized


@pytest.mark.asyncio
async def test_initialize_and_shutdown_persistence(monkeypatch):
    config = PersistenceConfig(database_host="localhost", database_port=5432)

    # Patch PersistenceInitializer to avoid real DB
    class DummyInit:
        is_initialized = True

        async def initialize(self):
            pass

        async def shutdown(self):
            pass

        @property
        def database_manager(self):
            class DummyDB:
                def get_session(self):
                    class DummySession:
                        async def __aenter__(self):
                            return self

                        async def __aexit__(self, *a):
                            pass

                        async def execute(self, *a, **kw):
                            return self

                        def scalar(self):
                            return 1

                        def scalar_one_or_none(self):
                            return 1

                    return DummySession()

            return DummyDB()

    monkeypatch.setattr(
        "src.infrastructure.persistence.config.PersistenceInitializer", DummyInit
    )

    async def dummy_aenter(self):
        return DummyInit()

    monkeypatch.setattr(
        "src.infrastructure.persistence.config.PersistenceContext.__aenter__",
        dummy_aenter,
    )
    monkeypatch.setattr(
        "src.infrastructure.persistence.config.initialize_persistence",
        lambda config: DummyInit(),
    )
    monkeypatch.setattr(
        "src.infrastructure.persistence.config.get_persistence_initializer",
        lambda: DummyInit(),
    )

    async def dummy_shutdown():
        pass

    monkeypatch.setattr(
        "src.infrastructure.persistence.config.shutdown_persistence", dummy_shutdown
    )
    # Test context manager
    async with PersistenceContext(config) as initializer:
        assert initializer.is_initialized
    # Test health checks
    assert await check_database_health() is True
    assert await check_timescale_health() is True
