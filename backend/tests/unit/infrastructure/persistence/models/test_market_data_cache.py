import pytest

@pytest.mark.unit
class TestModels:
    def test_models_import(self):
        from boursa_vision.infrastructure.persistence.models.market_data_cache import Base
        assert Base is not None
