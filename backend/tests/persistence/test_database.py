def test_database_config_url():
    config = DatabaseConfig(
        host="dbhost",
        port=5433,
        database="somedb",
        username="bob",
        password="secret",
    )
    url = config.database_url
    assert url == "postgresql+asyncpg://bob:secret@dbhost:5433/somedb"

def test_setup_engine_events():
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    db_manager.create_engine()
    # Should not raise
    db_manager._setup_engine_events()

import pytest
import types
import contextlib

@pytest.mark.asyncio
async def test_get_session_error_handling(monkeypatch):
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    db_manager.create_engine()
    db_manager.create_session_factory()
    class DummySession:
        async def rollback(self):
            self.rolled_back = True
        async def close(self):
            self.closed = True
    dummy = DummySession()
    async def session_factory():
        return contextlib.AsyncExitStack()
    # Patch session_factory to yield dummy and raise
    @contextlib.asynccontextmanager
    async def broken_session():
        yield dummy
        raise Exception("fail")
    db_manager.create_session_factory = lambda: lambda: broken_session()
    with pytest.raises(Exception):
        async with db_manager.get_session() as session:
            assert session is dummy
import pytest
import asyncio
from src.infrastructure.persistence.database import DatabaseConfig, DatabaseManager

@pytest.mark.asyncio
async def test_database_manager_lifecycle():
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="test_db",
        username="user",
        password="pass",
        echo=False,
    )
    db_manager = DatabaseManager(config)
    # Engine and session factory should be None initially
    assert db_manager._engine is None
    assert db_manager._session_factory is None
    # Create engine and session factory
    engine = db_manager.create_engine()
    assert engine is not None
    session_factory = db_manager.create_session_factory()
    assert session_factory is not None
    # get_session returns a context manager
    async with db_manager.get_session() as session:
        assert session is not None
    # Closing should reset engine and session factory
    await db_manager.close()
    assert db_manager._engine is None
    assert db_manager._session_factory is None
