import pytest

@pytest.mark.unit
class TestFactory:
    def test_factory_import(self):
        from boursa_vision.infrastructure.persistence.factory import IRepositoryFactory
        assert IRepositoryFactory is not None
