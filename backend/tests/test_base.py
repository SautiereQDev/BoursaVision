import pytest

from infrastructure.persistence.models.base import Base


def test_base_example():
    # Exemple de test pour base
    base = Base()
    assert base is not None


def test_base_model():
    base = Base()
    assert base is not None
