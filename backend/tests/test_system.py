import pytest

from src.infrastructure.persistence.models.system import SystemConfig


def test_system_example():
    # Exemple de test pour system
    system = SystemConfig(
        key="Sample Key", value={"sample": "data"}, description="Sample description"
    )
    assert system.key == "Sample Key"
    assert system.value == {"sample": "data"}
    assert system.description == "Sample description"


def test_system_creation():
    # Test de création pour le modèle System
    system = SystemConfig(
        key="Test Key", value={"example": "data"}, description="Description de test"
    )
    assert system.key == "Test Key"
    assert system.value == {"example": "data"}
    assert system.description == "Description de test"
