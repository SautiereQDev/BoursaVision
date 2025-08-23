"""Tests pour client factory"""
import pytest

from boursa_vision.infrastructure.external.client_factory import ClientProfile


@pytest.mark.unit
class TestClientFactory:
    def test_client_profile_enum(self):
        """Test ClientProfile enum"""
        assert ClientProfile.DEVELOPMENT.value == "development"
        assert ClientProfile.TESTING.value == "testing"
