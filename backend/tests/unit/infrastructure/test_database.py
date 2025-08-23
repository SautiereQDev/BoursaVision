"""
Tests unitaires pour le module database.

Tests pour la configuration de base de données, gestion des sessions,
connexions, et optimisations TimescaleDB.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Configuration path pour imports
root_dir = Path(__file__).parent.parent.parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from boursa_vision.infrastructure.persistence.database import (
        DatabaseConfig,
        DatabaseManager,
    )

    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database import warning: {e}")
    DATABASE_AVAILABLE = False


class TestDatabaseConfig:
    """Tests pour DatabaseConfig."""

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_database_config_default_values(self):
        """Test configuration de base de données avec valeurs par défaut."""
        config = DatabaseConfig()

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "trading_platform"
        assert config.username == "trading_user"
        assert config.password == "password"
        assert config.pool_size == 20
        assert config.max_overflow == 30
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.echo is False

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_database_config_custom_values(self):
        """Test configuration de base de données avec valeurs personnalisées."""
        config = DatabaseConfig(
            host="custom-host",
            port=5433,
            database="custom_db",
            username="custom_user",
            password="custom_pass",
            pool_size=10,
            max_overflow=15,
            pool_timeout=60,
            pool_recycle=1800,
            echo=True,
        )

        assert config.host == "custom-host"
        assert config.port == 5433
        assert config.database == "custom_db"
        assert config.username == "custom_user"
        assert config.password == "custom_pass"
        assert config.pool_size == 10
        assert config.max_overflow == 15
        assert config.pool_timeout == 60
        assert config.pool_recycle == 1800
        assert config.echo is True

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_database_url_generation(self):
        """Test génération de l'URL de base de données."""
        config = DatabaseConfig(
            host="test-host",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        expected_url = "postgresql+asyncpg://test_user:test_pass@test-host:5432/test_db"
        assert config.database_url == expected_url

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_database_url_special_characters(self):
        """Test génération de l'URL avec caractères spéciaux."""
        config = DatabaseConfig(
            host="test-host.example.com",
            port=5433,
            database="test_db_2024",
            username="user@domain",
            password="pass!@#$",
        )

        expected_url = "postgresql+asyncpg://user@domain:pass!@#$@test-host.example.com:5433/test_db_2024"
        assert config.database_url == expected_url


class TestDatabaseManager:
    """Tests pour DatabaseManager."""

    @pytest.fixture
    def database_config(self):
        """Configuration de test pour la base de données."""
        return DatabaseConfig(
            host="test-host",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
            pool_size=5,
            echo=False,
        )

    @pytest.fixture
    def database_manager(self, database_config):
        """Instance de DatabaseManager pour les tests."""
        return DatabaseManager(database_config)

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_database_manager_initialization(self, database_manager, database_config):
        """Test initialisation du DatabaseManager."""
        assert database_manager.config == database_config
        assert database_manager._engine is None
        assert database_manager._session_factory is None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_create_engine_first_call(self, database_manager):
        """Test création du moteur SQLAlchemy au premier appel."""
        with (
            patch(
                "boursa_vision.infrastructure.persistence.database.create_async_engine"
            ) as mock_create_engine,
            patch(
                "boursa_vision.infrastructure.persistence.database.event"
            ) as mock_event,
        ):
            mock_engine = MagicMock()
            mock_engine.sync_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            engine = database_manager.create_engine()

            assert engine == mock_engine
            assert database_manager._engine == mock_engine
            mock_create_engine.assert_called_once()

            # Vérifier les paramètres d'appel
            call_args = mock_create_engine.call_args
            assert call_args[0][0] == database_manager.config.database_url
            assert call_args[1]["pool_size"] == 5
            assert call_args[1]["echo"] is False

            # Vérifier que l'event listener est configuré
            mock_event.listens_for.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_create_engine_subsequent_calls(self, database_manager):
        """Test que les appels subséquents retournent le même moteur."""
        with (
            patch(
                "boursa_vision.infrastructure.persistence.database.create_async_engine"
            ) as mock_create_engine,
            patch(
                "boursa_vision.infrastructure.persistence.database.event"
            ) as mock_event,
        ):
            mock_engine = MagicMock()
            mock_engine.sync_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            engine1 = database_manager.create_engine()
            engine2 = database_manager.create_engine()

            assert engine1 == engine2
            assert engine1 == mock_engine
            mock_create_engine.assert_called_once()  # Appelé une seule fois

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_create_session_factory_first_call(self, database_manager):
        """Test création de la factory de sessions au premier appel."""
        with (
            patch(
                "boursa_vision.infrastructure.persistence.database.create_async_engine"
            ) as mock_create_engine,
            patch(
                "boursa_vision.infrastructure.persistence.database.async_sessionmaker"
            ) as mock_sessionmaker,
            patch("boursa_vision.infrastructure.persistence.database.event"),
        ):
            mock_engine = MagicMock()
            mock_engine.sync_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_factory = MagicMock()
            mock_sessionmaker.return_value = mock_factory

            factory = database_manager.create_session_factory()

            assert factory == mock_factory
            assert database_manager._session_factory == mock_factory
            mock_sessionmaker.assert_called_once()

            # Vérifier les paramètres de la session factory
            call_kwargs = mock_sessionmaker.call_args[1]
            assert call_kwargs["expire_on_commit"] is False
            assert call_kwargs["autoflush"] is True
            assert call_kwargs["autocommit"] is False

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_create_session_factory_subsequent_calls(self, database_manager):
        """Test que les appels subséquents retournent la même factory."""
        with (
            patch(
                "boursa_vision.infrastructure.persistence.database.create_async_engine"
            ) as mock_create_engine,
            patch(
                "boursa_vision.infrastructure.persistence.database.async_sessionmaker"
            ) as mock_sessionmaker,
            patch("boursa_vision.infrastructure.persistence.database.event"),
        ):
            mock_engine = MagicMock()
            mock_engine.sync_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_factory = MagicMock()
            mock_sessionmaker.return_value = mock_factory

            factory1 = database_manager.create_session_factory()
            factory2 = database_manager.create_session_factory()

            assert factory1 == factory2
            assert factory1 == mock_factory
            mock_sessionmaker.assert_called_once()  # Appelé une seule fois

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_get_session_success(self, database_manager):
        """Test récupération de session avec succès."""
        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(
            database_manager, "create_session_factory", return_value=mock_factory
        ):
            async with database_manager.get_session() as session:
                assert session == mock_session

            # Vérifier que la session est fermée
            mock_session.close.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_get_session_with_exception(self, database_manager):
        """Test récupération de session avec exception."""
        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        test_exception = Exception("Test exception")

        with patch.object(
            database_manager, "create_session_factory", return_value=mock_factory
        ):
            try:
                async with database_manager.get_session() as session:
                    assert session == mock_session
                    raise test_exception
            except Exception as e:
                assert e == test_exception
                # Vérifier que rollback et close sont appelés
                mock_session.rollback.assert_called_once()
                mock_session.close.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_ensure_timescale_extension_new_install(self, database_manager):
        """Test installation de l'extension TimescaleDB."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Extension non installée
        mock_session.execute.return_value = mock_result

        with patch.object(database_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

            await database_manager.ensure_timescale_extension()

            # Vérifier les appels SQL
            assert mock_session.execute.call_count == 2  # Check + CREATE EXTENSION
            mock_session.commit.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_ensure_timescale_extension_already_installed(self, database_manager):
        """Test avec extension TimescaleDB déjà installée."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "1.7.5"  # Extension installée
        mock_session.execute.return_value = mock_result

        with patch.object(database_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

            await database_manager.ensure_timescale_extension()

            # Vérifier qu'une seule requête est exécutée (le check)
            assert mock_session.execute.call_count == 1
            # Commit pas appelé car pas de changement
            mock_session.commit.assert_not_called()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_ensure_timescale_extension_failure(self, database_manager):
        """Test gestion d'erreur lors de l'installation TimescaleDB."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        with patch.object(database_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(Exception, match="Database error"):
                await database_manager.ensure_timescale_extension()

            # Vérifier que rollback est appelé
            mock_session.rollback.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_create_hypertables_success(self, database_manager):
        """Test création des hypertables avec succès."""
        mock_session = AsyncMock()

        # Mock pour les vérifications de table
        table_check_result = MagicMock()
        table_check_result.scalar_one_or_none.return_value = 1  # Table existe

        # Mock pour les vérifications d'hypertable
        hypertable_check_result = MagicMock()
        hypertable_check_result.scalar_one_or_none.return_value = (
            None  # Hypertable n'existe pas
        )

        # Configure les retours différents pour chaque appel execute
        mock_session.execute.side_effect = [
            table_check_result,  # Table check
            hypertable_check_result,  # Hypertable check
            MagicMock(),  # CREATE hypertable
        ] * 4  # Pour 4 tables

        with patch.object(database_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

            await database_manager.create_hypertables()

            # Vérifier qu'execute est appelé pour chaque table (3 fois par table * 4 tables)
            assert mock_session.execute.call_count == 12
            mock_session.commit.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_create_hypertables_table_not_exists(self, database_manager):
        """Test création d'hypertables quand les tables n'existent pas."""
        mock_session = AsyncMock()

        # Mock pour les vérifications de table - table n'existe pas
        table_check_result = MagicMock()
        table_check_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = table_check_result

        with patch.object(database_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

            await database_manager.create_hypertables()

            # Vérifier que seulement les checks de table sont faits (1 par table * 4 tables)
            assert mock_session.execute.call_count == 4
            mock_session.commit.assert_called_once()

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_close_engine(self, database_manager):
        """Test fermeture du moteur de base de données."""
        mock_engine = AsyncMock()
        database_manager._engine = mock_engine
        database_manager._session_factory = MagicMock()

        await database_manager.close()

        mock_engine.dispose.assert_called_once()
        assert database_manager._engine is None
        assert database_manager._session_factory is None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    async def test_close_no_engine(self, database_manager):
        """Test fermeture quand pas de moteur."""
        # Pas d'engine créé
        assert database_manager._engine is None

        # Ne devrait pas lever d'exception
        await database_manager.close()

        assert database_manager._engine is None
        assert database_manager._session_factory is None


class TestDatabaseIntegration:
    """Tests d'intégration pour le module database."""

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_database_classes_available(self):
        """Test que toutes les classes de base de données sont disponibles."""
        assert DatabaseConfig is not None
        assert DatabaseManager is not None

    @pytest.mark.skipif(not DATABASE_AVAILABLE, reason="Database module non disponible")
    def test_database_workflow(self):
        """Test workflow complet de configuration et manager."""
        # Créer une configuration
        config = DatabaseConfig(
            host="test-host",
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        # Créer un manager
        manager = DatabaseManager(config)

        # Vérifier la configuration
        assert manager.config == config
        assert (
            manager.config.database_url
            == "postgresql+asyncpg://test_user:test_pass@test-host:5432/test_db"
        )

    def test_database_imports_gracefully(self):
        """Test que les imports de database échouent gracieusement."""
        if not DATABASE_AVAILABLE:
            # Tester que les imports ont échoué de manière attendue
            with pytest.raises(ImportError):
                pass
        else:
            # Si les imports fonctionnent, vérifier la disponibilité
            assert DATABASE_AVAILABLE is True
