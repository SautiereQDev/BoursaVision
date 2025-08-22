import pytest

@pytest.mark.unit
class TestMocks:
    def test_mock_import(self):
        from boursa_vision.infrastructure.persistence.mock_repositories import MockUserRepository
        assert MockUserRepository is not None
