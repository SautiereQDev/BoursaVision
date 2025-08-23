"""
Coverage tests for JWT Service - Phase 2
=========================================
Tests to improve JWT Service coverage from 87.7% to 95%+

Targeting missing lines: 201-213 (validate_access_token method)
"""

from datetime import datetime, timedelta

import jwt
import pytest

from boursa_vision.application.services.jwt_service import JWTService


class TestJWTServiceCoverage:
    """Test coverage improvements for JWTService"""

    @pytest.fixture
    def jwt_service(self):
        """JWTService fixture with test configuration"""
        return JWTService(
            secret_key="test_secret_key_for_coverage_testing",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )

    def test_validate_access_token_valid_token(self, jwt_service):
        """Test validate_access_token with valid token (lines 208-210)"""
        # Create a valid access token
        user_id = "test-user-123"
        email = "test@example.com"
        role = "user"
        permissions = ["read", "write"]

        token_obj = jwt_service.create_access_token(user_id, email, role, permissions)
        token_string = token_obj.token  # Extract the actual JWT string

        # Should return True for valid token
        result = jwt_service.validate_access_token(token_string)
        assert result is True

    def test_validate_access_token_invalid_token(self, jwt_service):
        """Test validate_access_token with invalid token (lines 211-213)"""
        # Test with completely invalid token
        invalid_token = "invalid.token.string"
        result = jwt_service.validate_access_token(invalid_token)
        assert result is False

    def test_validate_access_token_expired_token(self, jwt_service):
        """Test validate_access_token with expired token"""
        # Create expired token manually
        payload = {
            "user_id": "test-user",
            "token_type": "access",
            "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
        }
        expired_token = jwt.encode(
            payload, jwt_service.secret_key, algorithm=jwt_service.algorithm
        )

        # Should return False for expired token
        result = jwt_service.validate_access_token(expired_token)
        assert result is False

    def test_validate_access_token_wrong_token_type(self, jwt_service):
        """Test validate_access_token with refresh token (wrong type)"""
        # Create a refresh token instead of access token
        user_id = "test-user-123"
        refresh_token_obj = jwt_service.create_refresh_token(user_id)
        refresh_token_string = refresh_token_obj.token  # Extract JWT string

        # Should return False for wrong token type
        result = jwt_service.validate_access_token(refresh_token_string)
        assert result is False

    def test_validate_access_token_malformed_token(self, jwt_service):
        """Test validate_access_token with malformed token"""
        # Test with various malformed tokens
        malformed_tokens = [
            "",  # Empty string
            "not.enough.parts",  # Not enough JWT parts
            "too.many.parts.in.this.token",  # Too many parts
            "invalid_base64.invalid_base64.invalid_base64",  # Invalid base64
        ]

        for token in malformed_tokens:
            result = jwt_service.validate_access_token(token)
            assert result is False

    def test_validate_access_token_wrong_signature(self, jwt_service):
        """Test validate_access_token with token signed with different key"""
        # Create token with different secret
        different_service = JWTService(
            secret_key="different_secret_key",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )

        # Create token with different secret
        user_id = "test-user-123"
        email = "test@example.com"
        role = "user"
        permissions = ["read", "write"]

        token_obj = different_service.create_access_token(
            user_id, email, role, permissions
        )
        token_with_wrong_signature = token_obj.token  # Extract JWT string

        # Should return False when verified with original service
        result = jwt_service.validate_access_token(token_with_wrong_signature)
        assert result is False

    def test_validate_access_token_none_input(self, jwt_service):
        """Test validate_access_token with None input"""
        result = jwt_service.validate_access_token(None)
        assert result is False

    def test_validate_access_token_non_string_input(self, jwt_service):
        """Test validate_access_token with non-string input"""
        # Test with various non-string inputs
        non_string_inputs = [
            123,  # Integer
            [],  # List
            {},  # Dict
            object(),  # Object
        ]

        for input_value in non_string_inputs:
            result = jwt_service.validate_access_token(input_value)
            assert result is False
