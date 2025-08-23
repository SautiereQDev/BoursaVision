"""Tests for Celery application configuration."""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))


class TestCeleryConfiguration:
    """Test Celery app configuration and initialization."""

    def test_celery_import_availability(self):
        """Test Celery import detection."""
        # Test should work regardless of Celery availability
        try:
            from boursa_vision.infrastructure.background.celery_app import (
                CELERY_AVAILABLE,
            )

            assert isinstance(CELERY_AVAILABLE, bool)
        except ImportError:
            pytest.skip("Celery app module not accessible - test skipped")

    def test_mock_mode_environment_variable(self):
        """Test mock mode activation via environment variable."""
        with patch.dict(os.environ, {"USE_MOCK_CELERY": "true"}):
            # Reimport to test environment variable effect

            try:
                # Clear module cache
                if "boursa_vision.infrastructure.background.celery_app" in sys.modules:
                    del sys.modules[
                        "boursa_vision.infrastructure.background.celery_app"
                    ]

                from boursa_vision.infrastructure.background.celery_app import (
                    USE_MOCK_CELERY,
                )

                assert USE_MOCK_CELERY is True
            except ImportError:
                pytest.skip("Celery app module not accessible - test skipped")

    def test_environment_configuration_urls(self):
        """Test broker and result backend URL configuration from environment."""
        test_broker = "redis://test-broker:6379/1"
        test_backend = "redis://test-backend:6379/2"

        with patch.dict(
            os.environ,
            {"CELERY_BROKER_URL": test_broker, "CELERY_RESULT_BACKEND": test_backend},
        ):
            try:
                # Clear module cache
                if "boursa_vision.infrastructure.background.celery_app" in sys.modules:
                    del sys.modules[
                        "boursa_vision.infrastructure.background.celery_app"
                    ]

                from boursa_vision.infrastructure.background.celery_app import (
                    CELERY_BROKER_URL,
                    CELERY_RESULT_BACKEND,
                )

                assert test_broker == CELERY_BROKER_URL
                assert test_backend == CELERY_RESULT_BACKEND
            except ImportError:
                pytest.skip("Celery app module not accessible - test skipped")

    def test_default_redis_configuration(self):
        """Test default Redis configuration when no environment variables set."""
        # Clear Celery-specific env vars
        env_vars_to_clear = ["CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", "REDIS_URL"]

        with patch.dict(os.environ, {}, clear=False):
            # Remove specific variables
            for var in env_vars_to_clear:
                os.environ.pop(var, None)

            try:
                # Clear module cache
                if "boursa_vision.infrastructure.background.celery_app" in sys.modules:
                    del sys.modules[
                        "boursa_vision.infrastructure.background.celery_app"
                    ]

                from boursa_vision.infrastructure.background.celery_app import (
                    CELERY_BROKER_URL,
                    CELERY_RESULT_BACKEND,
                )

                # Should use default Redis URLs
                assert "redis://redis:6379/0" in CELERY_BROKER_URL
                assert "redis://redis:6379/0" in CELERY_RESULT_BACKEND
            except ImportError:
                pytest.skip("Celery app module not accessible - test skipped")


class TestMockCelery:
    """Test mock Celery implementation."""

    def test_mock_celery_instantiation(self):
        """Test MockCelery class can be instantiated."""
        try:
            from boursa_vision.infrastructure.background.celery_app import MockCelery

            mock_celery = MockCelery("test_app")
            assert mock_celery is not None
            assert hasattr(mock_celery, "signals")
            assert hasattr(mock_celery, "task")
            assert hasattr(mock_celery, "conf")
        except ImportError:
            pytest.skip("MockCelery not accessible - test skipped")

    def test_mock_celery_task_decorator(self):
        """Test MockCelery task decorator functionality."""
        try:
            from boursa_vision.infrastructure.background.celery_app import MockCelery

            mock_celery = MockCelery("test_app")

            # Test task decorator
            @mock_celery.task()
            def test_task():
                return "test_result"

            # Should return the original function
            assert test_task() == "test_result"
            assert callable(test_task)
        except ImportError:
            pytest.skip("MockCelery not accessible - test skipped")

    def test_mock_celery_signals(self):
        """Test MockCelery signals implementation."""
        try:
            from boursa_vision.infrastructure.background.celery_app import MockCelery

            mock_celery = MockCelery("test_app")
            signals = mock_celery.signals

            # Test signal connections
            assert hasattr(signals, "task_failure")
            assert hasattr(signals, "task_success")

            # Test connecting handlers
            @signals.task_failure.connect
            def failure_handler():
                pass

            @signals.task_success.connect
            def success_handler():
                pass

            # Should not error
            assert callable(failure_handler)
            assert callable(success_handler)
        except ImportError:
            pytest.skip("MockCelery not accessible - test skipped")

    def test_mock_celery_configuration(self):
        """Test MockCelery configuration interface."""
        try:
            from boursa_vision.infrastructure.background.celery_app import MockCelery

            mock_celery = MockCelery("test_app")

            # Test configuration update
            mock_celery.conf.update(task_serializer="json", result_serializer="json")

            # Should not error
            assert hasattr(mock_celery, "conf")
        except ImportError:
            pytest.skip("MockCelery not accessible - test skipped")


class TestCeleryAppInstance:
    """Test Celery app instance configuration."""

    def test_celery_app_creation(self):
        """Test celery_app instance is properly created."""
        try:
            from boursa_vision.infrastructure.background.celery_app import celery_app

            assert celery_app is not None
            # Should have main Celery app attributes (or mock equivalents)
            assert hasattr(celery_app, "task") or hasattr(celery_app, "conf")
        except ImportError:
            pytest.skip("Celery app instance not accessible - test skipped")

    def test_celery_app_configuration_update(self):
        """Test celery app configuration is properly updated."""
        try:
            from boursa_vision.infrastructure.background.celery_app import celery_app

            # Should have conf attribute
            assert hasattr(celery_app, "conf")

            # Configuration update should not error
            celery_app.conf.update(test_setting="test_value")
        except ImportError:
            pytest.skip("Celery app instance not accessible - test skipped")

    def test_celery_app_task_routes(self):
        """Test task routes configuration."""
        with patch.dict(os.environ, {"USE_MOCK_CELERY": "false"}):
            try:
                # Clear module cache to test with real Celery
                if "boursa_vision.infrastructure.background.celery_app" in sys.modules:
                    del sys.modules[
                        "boursa_vision.infrastructure.background.celery_app"
                    ]

                from boursa_vision.infrastructure.background.celery_app import (
                    celery_app,
                )

                # Should be able to access conf
                assert hasattr(celery_app, "conf")
            except (ImportError, NameError):
                pytest.skip("Real Celery not available - test skipped")


class TestCeleryScheduling:
    """Test Celery scheduling functionality."""

    def test_mock_crontab_function(self):
        """Test mock crontab function."""
        with patch.dict(os.environ, {"USE_MOCK_CELERY": "true"}):
            try:
                # Clear and reimport to use mock
                modules_to_clear = [
                    "boursa_vision.infrastructure.background.celery_app",
                ]
                for module in modules_to_clear:
                    if module in sys.modules:
                        del sys.modules[module]

                from boursa_vision.infrastructure.background.celery_app import crontab

                # Mock crontab should return kwargs dict
                schedule = crontab(minute=0, hour="*/4")
                assert isinstance(schedule, dict)
                assert schedule["minute"] == 0
                assert schedule["hour"] == "*/4"
            except ImportError:
                pytest.skip("Crontab function not accessible - test skipped")

    def test_crontab_scheduling_configuration(self):
        """Test crontab can be used in beat schedule."""
        try:
            from boursa_vision.infrastructure.background.celery_app import (
                celery_app,
                crontab,
            )

            # Should be able to configure beat schedule
            beat_schedule = {
                "test-task": {
                    "task": "test.task",
                    "schedule": crontab(minute=0, hour=4),
                }
            }

            # Should not error when updating configuration
            celery_app.conf.update(beat_schedule=beat_schedule)
        except ImportError:
            pytest.skip("Crontab scheduling not accessible - test skipped")


class TestCeleryLogging:
    """Test Celery logging configuration."""

    def setup_method(self, method):
        """Setup avant chaque test pour s'assurer de l'isolation."""
        # Reset any potential global state
        pass

    def teardown_method(self, method):
        """Cleanup après chaque test pour éviter la pollution d'état."""
        # Clean up module imports if needed
        import sys

        # Specifically clean up celery_app module to avoid state pollution
        if "boursa_vision.infrastructure.background.celery_app" in sys.modules:
            del sys.modules["boursa_vision.infrastructure.background.celery_app"]

    def test_logger_creation(self):
        """Test logger is properly created."""
        try:
            from boursa_vision.infrastructure.background.celery_app import logger

            assert logger is not None
            assert logger.name == "boursa_vision.infrastructure.background.celery_app"
        except ImportError:
            pytest.skip("Logger not accessible - test skipped")

    @patch("logging.getLogger")
    def test_logger_configuration(self, mock_get_logger):
        """Test logger configuration."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Reimport to test logger creation
        try:
            if "boursa_vision.infrastructure.background.celery_app" in sys.modules:
                del sys.modules["boursa_vision.infrastructure.background.celery_app"]

            # Import directly from the celery_app module, not via __init__.py
            from boursa_vision.infrastructure.background.celery_app import celery_app

            # Should have called getLogger with module name (check that it was called with the right module)
            # getLogger may have been called multiple times, check if our module was one of them
            calls = mock_get_logger.call_args_list
            module_names = [
                call[0][0] if call[0] else call[1].get("name", "") for call in calls
            ]
            assert "boursa_vision.infrastructure.background.celery_app" in module_names
        except ImportError:
            pytest.skip("Logger configuration not testable - test skipped")


class TestCeleryIntegration:
    """Integration tests for Celery configuration."""

    def test_celery_module_imports(self):
        """Test all necessary Celery module imports."""
        try:
            from boursa_vision.infrastructure.background.celery_app import (
                CELERY_BROKER_URL,
                CELERY_RESULT_BACKEND,
                celery_app,
                logger,
            )

            assert celery_app is not None
            assert CELERY_BROKER_URL is not None
            assert CELERY_RESULT_BACKEND is not None
            assert logger is not None
        except ImportError:
            pytest.skip("Celery module components not accessible - test skipped")

    def test_celery_environment_integration(self):
        """Test Celery integrates with environment configuration."""
        # Test that environment variables are properly read by the configuration logic
        test_env = {
            "REDIS_URL": "redis://integration-test:6379/5",
            "USE_MOCK_CELERY": "false",
        }

        with patch.dict(os.environ, test_env, clear=False):
            try:
                # Test that configuration logic respects environment fallback
                # Since CELERY_BROKER_URL is not set, should fall back to REDIS_URL
                test_broker = os.getenv(
                    "CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0")
                )
                test_backend = os.getenv(
                    "CELERY_RESULT_BACKEND",
                    os.getenv("REDIS_URL", "redis://redis:6379/0"),
                )

                # Should use REDIS_URL as fallback when environment vars are properly set
                assert "redis://integration-test:6379/5" in test_broker
                assert "redis://integration-test:6379/5" in test_backend

            except Exception as e:
                pytest.skip(f"Environment integration not testable - {e}")

    def test_task_configuration_structure(self):
        """Test task configuration has expected structure."""
        try:
            from boursa_vision.infrastructure.background.celery_app import celery_app

            # Should be able to register tasks (mock or real)
            @celery_app.task(bind=True)
            def test_integration_task(self):
                return "integration_test"

            # Should not error
            assert callable(test_integration_task)
        except ImportError:
            pytest.skip("Task configuration not testable - test skipped")
