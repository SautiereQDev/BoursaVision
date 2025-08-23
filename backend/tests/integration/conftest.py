"""
Configuration Pytest pour les tests d'intégration
==============================================

Fixtures pour les tests d'intégration avec SQLAlchemy et base de données de test.
Utilise SQLite en mémoire pour des tests rapides et isolés.
"""

import asyncio
import contextlib
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Import des modèles nécessaires
# Base sera importé dynamiquement dans les fixtures
try:
    from boursa_vision.infrastructure.persistence.models.investment import (
        InvestmentModel,
    )
    from boursa_vision.infrastructure.persistence.models.users import User as UserModel
except ImportError:
    # Les imports échoueront dans l'IDE mais fonctionneront à l'exécution
    pass


# Configure pytest-asyncio mode
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Event loop pour les tests async avec proper cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Proper cleanup of all pending tasks
    pending_tasks = asyncio.all_tasks(loop)
    if pending_tasks:
        for task in pending_tasks:
            task.cancel()
        await asyncio.gather(*pending_tasks, return_exceptions=True)

    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Moteur de base de données SQLite en mémoire pour les tests.

    Utilise SQLite en mémoire pour les tests rapides et isolés.
    Compatible seulement avec les modèles sans types PostgreSQL spécifiques.
    """
    # Utiliser une base temporaire partagée au lieu de :memory: pour éviter les problèmes de connexions multiples
    import os
    import tempfile

    # Créer un fichier temporaire pour la base de test
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # Fermer le descripteur, on utilisera seulement le chemin

    database_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(
        database_url,
        echo=False,  # Désactiver les logs SQL
        connect_args={
            "check_same_thread": False,  # Nécessaire pour SQLite async
        },
        future=True,
    )

    try:
        # Créer seulement les tables compatibles avec SQLite
        async with engine.begin() as conn:
            # Créer seulement la table investments manuellement pour éviter JSONB
            await conn.execute(
                text(
                    """
                CREATE TABLE investments (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    exchange VARCHAR(50) NOT NULL,
                    sector VARCHAR(100),
                    industry VARCHAR(100),
                    market_cap DECIMAL(20, 2),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )

        yield engine

    finally:
        # Nettoyer l'engine
        await engine.dispose()
        # Supprimer le fichier temporaire
        with contextlib.suppress(OSError):
            os.unlink(db_path)


@pytest_asyncio.fixture
async def test_session(
    test_db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Session de base de données pour les tests avec proper cleanup.

    Chaque test reçoit une session fraîche qui utilise la base en mémoire.
    La session est correctement fermée après chaque test.

    Args:
        test_db_engine: Le moteur de base de données de test

    Yields:
        AsyncSession: Session SQLAlchemy pour le test
    """
    # Créer une nouvelle session pour chaque test
    async_session = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        try:
            yield session
            # Commit any pending transactions
            await session.commit()
        except Exception:
            # Rollback on error
            await session.rollback()
            raise
        finally:
            # Ensure session is properly closed
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def clean_db(test_session: AsyncSession) -> None:
    """
    Nettoie la base de données avant chaque test.

    Cette fixture s'assure que chaque test démarre avec une base vide.
    Utilisée principalement pour les tests qui nécessitent un état propre.

    Args:
        test_session: Session de base de données de test
    """
    # Vider la table investments (seule table créée dans les tests d'intégration)
    from boursa_vision.infrastructure.persistence.models.investment import (
        InvestmentModel,
    )

    await test_session.execute(InvestmentModel.__table__.delete())
    await test_session.commit()
