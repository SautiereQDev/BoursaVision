"""
Test simple pour vérifier le bon fonctionnement des factories et du conftest.py.

Ce test s'assure que la configuration de base fonctionne
avant de continuer avec des tests plus complexes.
"""

import pytest


@pytest.mark.fast
@pytest.mark.unit
def test_basic_fixtures_work(test_config, sample_user_data):
    """Test que les fixtures de base fonctionnent."""
    assert test_config is not None
    assert test_config["testing"] is True
    assert sample_user_data is not None
    assert sample_user_data["id"] == "test-user-123"


@pytest.mark.fast
@pytest.mark.unit  
def test_mock_services_work(mock_yfinance_client, mock_email_service, mock_celery_app):
    """Test que les services mockés sont disponibles."""
    assert mock_yfinance_client is not None
    assert mock_email_service is not None
    assert mock_celery_app is not None


@pytest.mark.fast
@pytest.mark.unit
async def test_async_fixtures_work(async_test_client):
    """Test que les fixtures async fonctionnent."""
    assert async_test_client is not None
    # Test d'un appel async basique
    result = await async_test_client.get("/test")
    assert result is not None


@pytest.mark.medium
@pytest.mark.integration
def test_core_container_available(core_container):
    """Test que le container core est disponible si possible."""
    # Ce test sera skippé si le container n'est pas disponible
    assert core_container is not None


@pytest.mark.medium
@pytest.mark.integration
def test_database_container_available(database_container):
    """Test que le container database est disponible si possible."""
    # Ce test sera skippé si le container n'est pas disponible
    assert database_container is not None
