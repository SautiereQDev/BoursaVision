"""
Tests d'intégration pour le point d'entrée principal de l'application.

Ces tests vérifient que le démarrage de l'application fonctionne correctement
dans différents environnements et configurations.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestMainIntegration:
    """Tests d'intégration pour le point d'entrée principal."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Configure l'environnement de test."""
        # S'assurer que le module main est accessible
        backend_dir = Path(__file__).parent.parent.parent
        src_dir = backend_dir / "src"

        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        # Nettoyer l'environnement après le test
        yield

        # Restaurer si nécessaire

    def test_setup_paths_adds_correct_directories(self):
        """Test que setup_paths ajoute les bons répertoires au sys.path."""
        # Import dynamique pour éviter les erreurs de chemin au chargement
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import setup_paths
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        original_path = sys.path.copy()
        try:
            setup_paths()
            # Vérifier que les chemins ont été ajoutés
            assert any("src" in path for path in sys.path), (
                "src directory should be in sys.path"
            )
        finally:
            # Nettoyer
            sys.path = original_path

    def test_detect_environment_default_configuration(self):
        """Test la détection d'environnement avec configuration par défaut."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import detect_environment
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        with (
            patch.dict(os.environ, {}, clear=False),
            patch("os.path.exists", return_value=False),
        ):
            config = detect_environment()

            assert config["host"] == "0.0.0.0"
            assert config["port"] == 8000  # Valeur par défaut
            assert config["reload"] is True  # Mode local par défaut

    def test_detect_environment_docker_mode(self):
        """Test la détection d'environnement en mode Docker."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import detect_environment
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # Simuler environnement Docker
        with (
            patch("os.path.exists", return_value=True),  # /.dockerenv existe
            patch.dict(os.environ, {"API_PORT": "9000", "API_RELOAD": "false"}),
        ):
            config = detect_environment()

            assert config["host"] == "0.0.0.0"
            assert config["port"] == 9000
            assert config["reload"] is False

    def test_detect_environment_docker_env_variable(self):
        """Test la détection Docker via variable d'environnement."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import detect_environment
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        with (
            patch("os.path.exists", return_value=False),
            patch.dict(os.environ, {"DOCKER_ENV": "true", "API_PORT": "8080"})
        ):
                config = detect_environment()

                assert config["host"] == "0.0.0.0"
                assert config["port"] == 8080
                assert config["reload"] is False  # Par défaut en Docker

    def test_detect_environment_local_mode(self):
        """Test la détection d'environnement en mode local."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import detect_environment
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        with (
            patch("os.path.exists", return_value=False),
            patch.dict(os.environ, {"API_PORT": "8001"}, clear=False)
        ):
                config = detect_environment()

                assert config["host"] == "0.0.0.0"
                assert config["port"] == 8001
                assert config["reload"] is True  # Toujours True en mode local

    @patch("sys.exit")
    def test_create_app_import_error(self, mock_exit):
        """Test la gestion des erreurs d'import dans create_app."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import create_app
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # Simuler une erreur d'import dans create_app
        with patch("boursa_vision.main.setup_paths"), patch(
            "builtins.__import__", side_effect=ImportError("Module not found")
        ):
            create_app()

            mock_exit.assert_called_once_with(1)

    def test_create_app_success(self):
        """Test la création réussie de l'application."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import create_app
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # Mock du module fastapi_yfinance
        mock_app = MagicMock()

        with patch("boursa_vision.main.setup_paths"), patch.dict(
            "sys.modules", {"fastapi_yfinance": MagicMock(app=mock_app)}
        ):
            app = create_app()

            assert app is mock_app

    @patch("uvicorn.run")
    def test_main_production_mode(self, mock_uvicorn_run):
        """Test le démarrage en mode production."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import main
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # Mock de l'app et de la configuration
        mock_app = MagicMock()

        with (
            patch("boursa_vision.main.detect_environment") as mock_detect_env,
            patch("boursa_vision.main.create_app", return_value=mock_app),
            patch("os.path.exists", return_value=False)
        ):
                    # Configuration mode production (reload=False)
                    mock_detect_env.return_value = {
                        "host": "0.0.0.0",
                        "port": 8000,
                        "reload": False,
                    }

                    main()

                    # Vérifier qu'uvicorn.run a été appelé avec l'app directement
                    mock_uvicorn_run.assert_called_once_with(
                        mock_app, host="0.0.0.0", port=8000, reload=False
                    )

    @patch("uvicorn.run")
    def test_main_development_mode_local(self, mock_uvicorn_run):
        """Test le démarrage en mode développement local."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import main
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        with (
            patch("boursa_vision.main.detect_environment") as mock_detect_env,
            patch("os.path.exists", return_value=False)  # Pas dans Docker
        ):
                # Configuration mode développement local
                mock_detect_env.return_value = {
                    "host": "0.0.0.0",
                    "port": 8001,
                    "reload": True,
                }

                main()

                # Vérifier qu'uvicorn.run a été appelé avec le string d'import
                mock_uvicorn_run.assert_called_once_with(
                    "src.fastapi_yfinance:app",
                    host="0.0.0.0",
                    port=8001,
                    reload=True,
                    reload_dirs=["src/"],
                    log_level="debug",
                )

    @patch("uvicorn.run")
    def test_main_development_mode_docker(self, mock_uvicorn_run):
        """Test le démarrage en mode développement Docker."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import main
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        with (
            patch("boursa_vision.main.detect_environment") as mock_detect_env,
            patch("os.path.exists", return_value=True)  # Dans Docker
        ):
                # Configuration mode développement Docker
                mock_detect_env.return_value = {
                    "host": "0.0.0.0",
                    "port": 8000,
                    "reload": True,
                }

                main()

                # Vérifier qu'uvicorn.run a été appelé avec les chemins Docker
                mock_uvicorn_run.assert_called_once_with(
                    "src.fastapi_yfinance:app",
                    host="0.0.0.0",
                    port=8000,
                    reload=True,
                    reload_dirs=["/app/src"],
                    log_level="debug",
                )

    @patch("sys.exit")
    def test_main_handles_startup_errors(self, mock_exit):
        """Test la gestion des erreurs de démarrage."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import main
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        with patch(
            "boursa_vision.main.detect_environment",
            side_effect=Exception("Config error"),
        ):
            main()

            mock_exit.assert_called_once_with(1)

    def test_environment_variable_parsing(self):
        """Test le parsing correct des variables d'environnement."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import detect_environment
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # Test avec port valide
        with (
            patch.dict(os.environ, {"API_PORT": "3000"}),
            patch("os.path.exists", return_value=False)
        ):
                config = detect_environment()
                assert config["port"] == 3000

        # Test avec port invalide (devrait lever une exception)
        with (
            patch.dict(os.environ, {"API_PORT": "invalid"}),
            patch("os.path.exists", return_value=False)
        ):
                with pytest.raises(ValueError):
                    detect_environment()


class TestMainIntegrationPathHandling:
    """Tests spécifiques à la gestion des chemins."""

    def test_path_resolution_consistency(self):
        """Test la cohérence de résolution des chemins."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import setup_paths
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # Sauvegarder l'état original
        original_path = sys.path.copy()

        try:
            # Appeler setup_paths plusieurs fois
            setup_paths()
            first_call_path = sys.path.copy()

            setup_paths()
            second_call_path = sys.path.copy()

            # Les chemins ne doivent pas être dupliqués
            assert len(first_call_path) == len(second_call_path)

        finally:
            sys.path = original_path

    def test_paths_are_absolute(self):
        """Test que tous les chemins ajoutés sont absolus."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import setup_paths
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        original_path = sys.path.copy()

        try:
            setup_paths()

            # Vérifier que les nouveaux chemins sont absolus
            new_paths = [p for p in sys.path if p not in original_path]
            for path in new_paths:
                assert Path(path).is_absolute(), f"Path {path} should be absolute"

        finally:
            sys.path = original_path


class TestMainIntegrationEnvironmentDetection:
    """Tests approfondis pour la détection d'environnement."""

    def test_docker_detection_precedence(self):
        """Test la précédence de détection Docker."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import detect_environment
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # File existe ET variable d'environnement
        with (
            patch("os.path.exists", return_value=True),
            patch.dict(os.environ, {"DOCKER_ENV": "false"})
        ):
                config = detect_environment()
                # Le fichier /.dockerenv a priorité
                assert config["reload"] is False  # Mode Docker détecté

    def test_environment_isolation(self):
        """Test l'isolation des variables d'environnement."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        try:
            from boursa_vision.main import detect_environment
        except ImportError:
            pytest.skip("Module main.py non accessible - test ignoré")

        # Nettoyer l'environnement pour ce test
        env_backup = os.environ.copy()

        try:
            # Supprimer toutes les variables pertinentes
            for key in ["API_PORT", "API_RELOAD", "DOCKER_ENV"]:
                os.environ.pop(key, None)

            with patch("os.path.exists", return_value=False):
                config = detect_environment()

                # Vérifier les valeurs par défaut
                assert config["port"] == 8000
                assert config["reload"] is True

        finally:
            os.environ.clear()
            os.environ.update(env_backup)
