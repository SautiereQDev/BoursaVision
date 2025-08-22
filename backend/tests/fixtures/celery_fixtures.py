"""
Fixtures pour les tests Celery.

Fournit des mocks et configurations pour tester l'infrastructure Celery
de manière isolée et reproductible.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_celery_app():
    """Mock d'une application Celery pour les tests unitaires."""
    mock_app = MagicMock()
    mock_app.task = MagicMock()
    mock_app.conf = MagicMock()
    mock_app.signals = MagicMock()
    mock_app.start = MagicMock()
    return mock_app


@pytest.fixture
def mock_celery_config():
    """Configuration Celery mockée pour les tests."""
    return {
        "broker_url": "redis://localhost:6379/0",
        "result_backend": "redis://localhost:6379/0",
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
    }


@pytest.fixture
def mock_environment_variables():
    """Mock des variables d'environnement pour Celery."""
    test_redis_url = "redis://test:6379/0"
    with patch.dict(
        "os.environ",
        {
            "CELERY_BROKER_URL": test_redis_url,
            "CELERY_RESULT_BACKEND": test_redis_url,
            "REDIS_URL": test_redis_url,
        },
        clear=False,
    ):
        yield


@pytest.fixture
def mock_crontab():
    """Mock de la fonction crontab pour les tests."""
    with patch("boursa_vision.infrastructure.background.celery_app.crontab") as mock:
        mock.return_value = {"minute": "*/5"}
        yield mock


@pytest.fixture
def mock_celery_logger():
    """Mock du logger Celery."""
    with patch("boursa_vision.infrastructure.background.celery_app.logger") as mock:
        yield mock
