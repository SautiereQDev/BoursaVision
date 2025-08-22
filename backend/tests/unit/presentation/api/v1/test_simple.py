"""
Test simple pour vérifier que pytest fonctionne
"""
import pytest


@pytest.mark.unit
def test_simple():
    """Test simple"""
    assert True


@pytest.mark.unit
class TestSimple:
    """Classe de test simple"""
    
    def test_method(self):
        """Test de méthode"""
        assert 1 + 1 == 2
