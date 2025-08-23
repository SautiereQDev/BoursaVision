"""
Tests unitaires pour la couche database SQLAlchemy avec TimescaleDB.

Tests complets pour DatabaseConfig, DatabaseManager, TimescaleDBManager
et les fonctions utilitaires de gestion de session.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

# Configuration path pour imports
root_dir = Path(__file__).parent.parent.parent.parent.parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from boursa_vision.application.exceptions import DatabaseNotInitializedError
    from boursa_vision.infrastructure.persistence.sqlalchemy.database import (
        DatabaseConfig,
        DatabaseManager,
        TimescaleDBManager,
        get_db_manager,
        get_db_session,
        get_timescale_manager,
        init_database,
    )

    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Import warning: {e}")
    DATABASE_AVAILABLE = False


class TestDatabaseConfig:
    """Tests pour DatabaseConfig."""

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_database_config_initialization(self):
        """Test de création de DatabaseConfig avec paramètres par défaut."""
        config = DatabaseConfig("postgresql://test")

        assert config.url == "postgresql://test"
        assert config.pool_size == 20
        assert config.max_overflow == 10
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.echo is False

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_database_config_custom_parameters(self):
        """Test de création de DatabaseConfig avec paramètres personnalisés."""
        config = DatabaseConfig(
            url="postgresql://custom",
            pool_size=5,
            max_overflow=15,
            pool_timeout=60,
            pool_recycle=7200,
            echo=True,
        )

        assert config.url == "postgresql://custom"
        assert config.pool_size == 5
        assert config.max_overflow == 15
        assert config.pool_timeout == 60
        assert config.pool_recycle == 7200
        assert config.echo is True


class TestDatabaseManager:
    """Tests pour DatabaseManager."""

    @pytest.fixture
    def db_config(self):
        """Fixture pour DatabaseConfig."""
        if DATABASE_AVAILABLE:
            return DatabaseConfig("postgresql://test")
        return None

    @pytest.fixture
    def db_manager(self, db_config):
        """Fixture pour DatabaseManager."""
        if DATABASE_AVAILABLE and db_config:
            return DatabaseManager(db_config)
        return None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_database_manager_initialization(self, db_manager, db_config):
        """Test de création de DatabaseManager."""
        assert db_manager is not None
        assert db_manager.config == db_config
        assert db_manager._engine is None
        assert db_manager._session_factory is None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_database_manager_initialize(self, db_manager):
        """Test d'initialisation du DatabaseManager."""
        with (
            patch(
                "boursa_vision.infrastructure.persistence.sqlalchemy.database.create_async_engine"
            ) as mock_engine,
            patch(
                "boursa_vision.infrastructure.persistence.sqlalchemy.database.async_sessionmaker"
            ) as mock_sessionmaker,
            patch("boursa_vision.infrastructure.persistence.sqlalchemy.database.event"),
        ):
            mock_async_engine = AsyncMock(spec=AsyncEngine)
            mock_engine.return_value = mock_async_engine

            await db_manager.initialize()

            assert db_manager._engine == mock_async_engine
            mock_engine.assert_called_once()
            mock_sessionmaker.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_database_manager_initialize_already_initialized(self, db_manager):
        """Test que initialize ne fait rien si déjà initialisé."""
        with patch(
            "boursa_vision.infrastructure.persistence.sqlalchemy.database.create_async_engine"
        ) as mock_engine:
            # Simuler que l'engine existe déjà
            db_manager._engine = MagicMock()

            await db_manager.initialize()

            # create_async_engine ne devrait pas être appelé
            mock_engine.assert_not_called()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_database_manager_close(self, db_manager):
        """Test de fermeture du DatabaseManager."""
        # Simuler un engine initialisé
        mock_engine = AsyncMock()
        db_manager._engine = mock_engine
        db_manager._session_factory = MagicMock()

        await db_manager.close()

        mock_engine.dispose.assert_called_once()
        assert db_manager._engine is None
        assert db_manager._session_factory is None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_database_manager_close_no_engine(self, db_manager):
        """Test de fermeture quand aucun engine n'est initialisé."""
        await db_manager.close()  # Ne devrait pas lever d'exception

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_database_manager_engine_property_not_initialized(self, db_manager):
        """Test d'accès à l'engine quand non initialisé."""
        with pytest.raises(DatabaseNotInitializedError):
            _ = db_manager.engine

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_database_manager_session_factory_property_not_initialized(
        self, db_manager
    ):
        """Test d'accès au session_factory quand non initialisé."""
        with pytest.raises(DatabaseNotInitializedError):
            _ = db_manager.session_factory

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_database_manager_engine_property_initialized(self, db_manager):
        """Test d'accès à l'engine quand initialisé."""
        mock_engine = MagicMock()
        db_manager._engine = mock_engine

        assert db_manager.engine == mock_engine

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_database_manager_session_factory_property_initialized(self, db_manager):
        """Test d'accès au session_factory quand initialisé."""
        mock_factory = MagicMock()
        db_manager._session_factory = mock_factory

        assert db_manager.session_factory == mock_factory

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_database_manager_session_context_manager_success(self, db_manager):
        """Test du gestionnaire de contexte session avec succès."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_factory.return_value.__aexit__.return_value = None

        db_manager._session_factory = mock_factory

        async with db_manager.session() as session:
            assert session == mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_database_manager_session_context_manager_error(self, db_manager):
        """Test du gestionnaire de contexte session avec erreur."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_factory.return_value.__aexit__.return_value = None

        db_manager._session_factory = mock_factory

        with pytest.raises(ValueError):
            async with db_manager.session() as session:
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestTimescaleDBManager:
    """Tests pour TimescaleDBManager."""

    @pytest.fixture
    def mock_db_manager(self):
        """Fixture pour DatabaseManager mocké."""
        if DATABASE_AVAILABLE:
            return MagicMock(spec=DatabaseManager)
        return None

    @pytest.fixture
    def timescale_manager(self, mock_db_manager):
        """Fixture pour TimescaleDBManager."""
        if DATABASE_AVAILABLE and mock_db_manager:
            return TimescaleDBManager(mock_db_manager)
        return None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_timescale_manager_initialization(self, timescale_manager, mock_db_manager):
        """Test de création de TimescaleDBManager."""
        assert timescale_manager.db_manager == mock_db_manager

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_create_hypertables_success(self, timescale_manager, mock_db_manager):
        """Test de création des hypertables avec succès."""
        # Mock session
        mock_session = AsyncMock()
        mock_db_manager.session.return_value.__aenter__.return_value = mock_session

        # Mock result pour simulate hypertable non existante
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        await timescale_manager.create_hypertables()

        # Vérifier que les requêtes ont été exécutées
        assert mock_session.execute.call_count > 0

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_create_hypertables_already_exists(
        self, timescale_manager, mock_db_manager
    ):
        """Test quand les hypertables existent déjà."""
        mock_session = AsyncMock()
        mock_db_manager.session.return_value.__aenter__.return_value = mock_session

        # Mock result pour simuler hypertable existante
        mock_result = MagicMock()
        mock_result.fetchone.return_value = {"hypertable_name": "market_data"}
        mock_session.execute.return_value = mock_result

        await timescale_manager.create_hypertables()

        # Les calls devraient être pour les vérifications uniquement
        assert (
            mock_session.execute.call_count >= 4
        )  # Au moins une vérification par table

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_create_hypertables_error(self, timescale_manager, mock_db_manager):
        """Test de gestion d'erreur lors de la création des hypertables."""
        mock_session = AsyncMock()
        mock_db_manager.session.return_value.__aenter__.return_value = mock_session

        # Simuler une erreur
        mock_session.execute.side_effect = SQLAlchemyError("Hypertable error")

        with pytest.raises(SQLAlchemyError):
            await timescale_manager.create_hypertables()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_create_performance_indexes(self, timescale_manager, mock_db_manager):
        """Test de création des indexes de performance."""
        mock_session = AsyncMock()
        mock_db_manager.session.return_value.__aenter__.return_value = mock_session

        await timescale_manager.create_performance_indexes()

        # Vérifier que plusieurs indexes ont été créés
        assert mock_session.execute.call_count >= 7  # Au moins 7 indexes

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_create_performance_indexes_with_errors(
        self, timescale_manager, mock_db_manager
    ):
        """Test de création d'indexes avec quelques erreurs (normales)."""
        mock_session = AsyncMock()
        mock_db_manager.session.return_value.__aenter__.return_value = mock_session

        # Simuler des erreurs sur quelques indexes (index déjà existants)
        mock_session.execute.side_effect = [
            None,  # Premier index OK
            SQLAlchemyError("Index already exists"),  # Deuxième index existe déjà
            None,  # Troisième index OK
            Exception("Other error"),  # Autre erreur
            None,  # Etc.
        ]

        # Ne devrait pas lever d'exception car les erreurs sont gérées
        await timescale_manager.create_performance_indexes()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_setup_compression(self, timescale_manager, mock_db_manager):
        """Test de configuration des politiques de compression."""
        mock_session = AsyncMock()
        mock_db_manager.session.return_value.__aenter__.return_value = mock_session

        await timescale_manager.setup_compression()

        # Vérifier que les politiques de compression ont été configurées
        assert mock_session.execute.call_count >= 4  # Au moins 4 tables

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_setup_compression_with_errors(
        self, timescale_manager, mock_db_manager
    ):
        """Test de configuration compression avec erreurs (politiques existantes)."""
        mock_session = AsyncMock()
        mock_db_manager.session.return_value.__aenter__.return_value = mock_session

        # Simuler des erreurs (politiques déjà existantes)
        mock_session.execute.side_effect = [
            Exception("Policy already exists") for _ in range(4)
        ]

        # Ne devrait pas lever d'exception car les erreurs sont gérées
        await timescale_manager.setup_compression()


class TestGlobalDatabaseFunctions:
    """Tests pour les fonctions globales de gestion de la base de données."""

    def setup_method(self):
        """Reset global managers before each test."""
        if DATABASE_AVAILABLE:
            # Reset global variables
            import boursa_vision.infrastructure.persistence.sqlalchemy.database as db_module

            db_module._db_manager = None
            db_module._timescale_manager = None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_init_database(self):
        """Test d'initialisation de la base de données globale."""
        config = DatabaseConfig("postgresql://test")

        init_database(config)

        # Vérifier que les managers globaux sont créés
        db_manager = get_db_manager()
        timescale_manager = get_timescale_manager()

        assert db_manager is not None
        assert timescale_manager is not None
        assert db_manager.config == config

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_get_db_manager_not_initialized(self):
        """Test d'accès au manager quand non initialisé."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_db_manager()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_get_timescale_manager_not_initialized(self):
        """Test d'accès au TimescaleDB manager quand non initialisé."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_timescale_manager()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_get_db_session_success(self):
        """Test du gestionnaire de contexte de session global."""
        # Initialiser la base
        config = DatabaseConfig("postgresql://test")
        init_database(config)

        # Mock du manager
        db_manager = get_db_manager()
        mock_session = AsyncMock(spec=AsyncSession)

        with patch.object(db_manager, "session") as mock_session_cm:
            mock_session_cm.return_value.__aenter__.return_value = mock_session
            mock_session_cm.return_value.__aexit__.return_value = None

            async with get_db_session() as session:
                assert session == mock_session

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_get_db_session_not_initialized(self):
        """Test du gestionnaire de session quand DB non initialisée."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            async with get_db_session() as session:
                pass


class TestDatabaseIntegration:
    """Tests d'intégration pour la couche database."""

    def setup_method(self):
        """Reset global managers before each test."""
        if DATABASE_AVAILABLE:
            import boursa_vision.infrastructure.persistence.sqlalchemy.database as db_module

            db_module._db_manager = None
            db_module._timescale_manager = None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_full_database_workflow(self):
        """Test du workflow complet d'initialisation et utilisation."""
        config = DatabaseConfig("postgresql://test", pool_size=5, echo=True)

        # 1. Initialiser
        init_database(config)

        # 2. Obtenir les managers
        db_manager = get_db_manager()
        timescale_manager = get_timescale_manager()

        assert db_manager.config.pool_size == 5
        assert db_manager.config.echo is True

        # 3. Mock initialization pour éviter vraie connexion DB
        with patch.object(db_manager, "initialize") as mock_init:
            await db_manager.initialize()
            mock_init.assert_called_once()

        # 4. Test session factory access (should fail if not initialized)
        with pytest.raises(DatabaseNotInitializedError):
            _ = db_manager.session_factory

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    def test_multiple_init_database_calls(self):
        """Test que plusieurs appels à init_database remplacent les managers."""
        config1 = DatabaseConfig("postgresql://test1")
        config2 = DatabaseConfig("postgresql://test2")

        init_database(config1)
        manager1 = get_db_manager()

        init_database(config2)
        manager2 = get_db_manager()

        assert manager1 is not manager2
        assert manager2.config.url == "postgresql://test2"

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module not available")
    @pytest.mark.asyncio
    async def test_timescale_operations_workflow(self):
        """Test du workflow TimescaleDB complet."""
        config = DatabaseConfig("postgresql://test")
        init_database(config)

        timescale_manager = get_timescale_manager()

        # Mock du db_manager pour éviter vraies connexions
        with patch.object(timescale_manager.db_manager, "session") as mock_session_cm:
            mock_session = AsyncMock()
            mock_session_cm.return_value.__aenter__.return_value = mock_session

            # Mock pour hypertables non existantes
            mock_result = MagicMock()
            mock_result.fetchone.return_value = None
            mock_session.execute.return_value = mock_result

            # Test des opérations TimescaleDB
            await timescale_manager.create_hypertables()
            await timescale_manager.create_performance_indexes()
            await timescale_manager.setup_compression()

            # Vérifier que des opérations ont été effectuées
            assert (
                mock_session.execute.call_count > 10
            )  # Hypertables + indexes + compression
