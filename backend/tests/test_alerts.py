import pytest

from src.infrastructure.persistence.models.alerts import Alert


def test_alerts_example():
    # Exemple de test pour alert
    alert = Alert(title="Test Alert", description="Description de test")
    assert alert.title == "Test Alert"
    assert alert.description == "Description de test"


def test_alert_model():
    alert = Alert()
    assert alert is not None
