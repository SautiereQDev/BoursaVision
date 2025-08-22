from src.infrastructure.persistence.models.performance import Performance


def test_performance_example():
    # Example test for performance
    assert 1 + 1 == 2


def test_performance_creation():
    # Test de création pour le modèle Performance
    performance = Performance(metric="Test Metric", value=100.0)
    assert performance.metric == "Test Metric"
    assert abs(performance.value - 100.0) < 1e-6
