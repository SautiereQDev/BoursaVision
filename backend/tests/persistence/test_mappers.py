import pytest

from src.infrastructure.persistence.mappers import MapperFactory


def test_mapper_factory_instance():
    factory = MapperFactory()
    assert factory is not None


# Ajoutez ici des tests unitaires pour les méthodes de MapperFactory si besoin
