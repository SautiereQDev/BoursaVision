"""
Test suite for JWT Service
==========================

Comprehensive unit tests for JWT token generation, validation, and management.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from boursa_vision.application.services.jwt_service import JWTService
from boursa_vision.domain.entities.user import UserRole
from boursa_vision.domain.value_objects.auth import AccessToken, RefreshToken, TokenPair


class TestJWTServiceInitialization:
    """Test JWT service initialization and configuration."""

    def test_jwt_service_initialization_default(self):
        """Test JWT service initialization with default values."""
        secret_key = "test-secret-key"
        service = JWTService(secret_key=secret_key)

        assert service.secret_key == secret_key
        assert service.algorithm == "HS256"
        assert service.access_token_expire_minutes == 30
        assert service.refresh_token_expire_days == 30

    def test_jwt_service_initialization_custom(self):
        """Test JWT service initialization with custom values."""
        secret_key = "custom-secret"
        algorithm = "HS512"
        access_expire = 60
        refresh_expire = 7

        service = JWTService(
            secret_key=secret_key,
            algorithm=algorithm,
            access_token_expire_minutes=access_expire,
            refresh_token_expire_days=refresh_expire,
        )

        assert service.secret_key == secret_key
        assert service.algorithm == algorithm
        assert service.access_token_expire_minutes == access_expire
        assert service.refresh_token_expire_days == refresh_expire

    def test_jwt_service_empty_secret_key_raises_error(self):
        """Test that empty secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            JWTService(secret_key="")

    def test_jwt_service_none_secret_key_raises_error(self):
        """Test that None secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            JWTService(secret_key=None)


class TestCreateAccessToken:
    """Test access token creation functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing."""
        return JWTService(secret_key="test-secret-key")

    @pytest.fixture
    def user_data(self):
        """Sample user data for token creation."""
        return {
            "user_id": uuid4(),
            "email": "test@example.com",
            "role": UserRole.VIEWER,
            "permissions": ["read", "write"],
        }

    def test_create_access_token_success(self, jwt_service, user_data):
        """Test successful access token creation."""
        token = jwt_service.create_access_token(**user_data)

        assert isinstance(token, AccessToken)
        assert token.user_id == user_data["user_id"]
        assert token.token_type == "Bearer"
        assert isinstance(token.issued_at, datetime)
        assert isinstance(token.expires_at, datetime)
        assert token.expires_at > token.issued_at

        # Verify token can be decoded
        payload = jwt.decode(
            token.token, jwt_service.secret_key, algorithms=[jwt_service.algorithm]
        )
        assert payload["sub"] == str(user_data["user_id"])
        assert payload["email"] == user_data["email"]
        assert payload["role"] == user_data["role"]
        assert payload["permissions"] == user_data["permissions"]
        assert payload["token_type"] == "access"
        assert "jti" in payload

    def test_create_access_token_with_custom_expiration(self, jwt_service, user_data):
        """Test access token creation with custom expiration."""
        custom_delta = timedelta(minutes=120)
        token = jwt_service.create_access_token(expires_delta=custom_delta, **user_data)

        expected_expiry = token.issued_at + custom_delta
        # Allow small time difference due to execution time
        assert abs((token.expires_at - expected_expiry).total_seconds()) < 1

    def test_create_access_token_with_extra_claims(self, jwt_service, user_data):
        """Test access token creation with extra claims."""
        extra_claims = {"department": "engineering", "level": "senior"}
        token = jwt_service.create_access_token(extra_claims=extra_claims, **user_data)

        payload = jwt.decode(
            token.token, jwt_service.secret_key, algorithms=[jwt_service.algorithm]
        )
        assert payload["department"] == "engineering"
        assert payload["level"] == "senior"

    def test_create_access_token_missing_user_id(self, jwt_service, user_data):
        """Test access token creation fails with missing user ID."""
        user_data["user_id"] = None

        with pytest.raises(ValueError, match="User ID is required"):
            jwt_service.create_access_token(**user_data)

    def test_create_access_token_missing_email(self, jwt_service, user_data):
        """Test access token creation fails with missing email."""
        user_data["email"] = None

        with pytest.raises(ValueError, match="Email is required"):
            jwt_service.create_access_token(**user_data)

    def test_create_access_token_empty_email(self, jwt_service, user_data):
        """Test access token creation fails with empty email."""
        user_data["email"] = ""

        with pytest.raises(ValueError, match="Email is required"):
            jwt_service.create_access_token(**user_data)

    def test_create_access_token_missing_role(self, jwt_service, user_data):
        """Test access token creation fails with missing role."""
        user_data["role"] = None

        with pytest.raises(ValueError, match="Role is required"):
            jwt_service.create_access_token(**user_data)


class TestCreateRefreshToken:
    """Test refresh token creation functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing."""
        return JWTService(secret_key="test-secret-key")

    def test_create_refresh_token_success(self, jwt_service):
        """Test successful refresh token creation."""
        user_id = uuid4()
        token = jwt_service.create_refresh_token(user_id=user_id)

        assert isinstance(token, RefreshToken)
        assert token.user_id == user_id
        assert isinstance(token.created_at, datetime)
        assert isinstance(token.expires_at, datetime)
        assert token.expires_at > token.created_at
        assert token.is_revoked is False

        # Verify token is URL-safe and long enough
        assert len(token.token) >= 64
        assert "+" not in token.token  # URL-safe doesn't contain +
        assert "/" not in token.token  # URL-safe doesn't contain /

    def test_create_refresh_token_custom_expiration(self):
        """Test refresh token creation with custom expiration."""
        jwt_service = JWTService(secret_key="test-secret", refresh_token_expire_days=7)
        user_id = uuid4()
        token = jwt_service.create_refresh_token(user_id)

        expected_expiry = token.created_at + timedelta(days=7)
        # Allow small time difference due to execution time
        assert abs((token.expires_at - expected_expiry).total_seconds()) < 1

    def test_create_refresh_token_randomness(self, jwt_service):
        """Test that refresh tokens are unique/random."""
        user_id = uuid4()
        token1 = jwt_service.create_refresh_token(user_id=user_id)
        token2 = jwt_service.create_refresh_token(user_id=user_id)

        assert token1.token != token2.token
        assert len({token1.token, token2.token}) == 2


class TestCreateTokenPair:
    """Test token pair creation functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing."""
        return JWTService(secret_key="test-secret-key")

    @pytest.fixture
    def user_data(self):
        """Sample user data for token creation."""
        return {
            "user_id": uuid4(),
            "email": "test@example.com",
            "role": UserRole.TRADER,
            "permissions": ["read", "write", "admin"],
        }

    def test_create_token_pair_success(self, jwt_service, user_data):
        """Test successful token pair creation."""
        token_pair = jwt_service.create_token_pair(**user_data)

        assert isinstance(token_pair, TokenPair)
        assert isinstance(token_pair.access_token, AccessToken)
        assert isinstance(token_pair.refresh_token, RefreshToken)

        # Both tokens should belong to the same user
        assert token_pair.access_token.user_id == user_data["user_id"]
        assert token_pair.refresh_token.user_id == user_data["user_id"]

    def test_create_token_pair_with_extra_claims(self, jwt_service, user_data):
        """Test token pair creation with extra claims in access token."""
        extra_claims = {"subscription": "premium", "features": ["analytics"]}
        token_pair = jwt_service.create_token_pair(
            extra_claims=extra_claims, **user_data
        )

        # Verify extra claims are in access token
        payload = jwt.decode(
            token_pair.access_token.token,
            jwt_service.secret_key,
            algorithms=[jwt_service.algorithm],
        )
        assert payload["subscription"] == "premium"
        assert payload["features"] == ["analytics"]


class TestVerifyAccessToken:
    """Test access token verification functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing."""
        return JWTService(secret_key="test-secret-key")

    @pytest.fixture
    def valid_token(self, jwt_service):
        """Create a valid access token for testing."""
        return jwt_service.create_access_token(
            user_id=uuid4(),
            email="test@example.com",
            role=UserRole.VIEWER,
            permissions=["read"],
        )

    def test_verify_access_token_success(self, jwt_service, valid_token):
        """Test successful access token verification."""
        payload = jwt_service.verify_access_token(valid_token.token)

        assert payload is not None
        assert payload["token_type"] == "access"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == UserRole.VIEWER
        assert payload["permissions"] == ["read"]
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_verify_access_token_invalid_signature(self, jwt_service, valid_token):
        """Test access token verification with invalid signature."""
        # Create service with different secret
        different_service = JWTService(secret_key="different-secret")
        payload = different_service.verify_access_token(valid_token.token)

        assert payload is None

    def test_verify_access_token_expired(self, jwt_service):
        """Test access token verification with expired token."""
        # Create token with short expiration that will expire
        token = jwt_service.create_access_token(
            user_id=uuid4(),
            email="test@example.com",
            role=UserRole.VIEWER,
            permissions=["read"],
            expires_delta=timedelta(seconds=0.001),  # Very short but not negative
        )

        # Wait a moment for token to expire
        import time

        time.sleep(0.01)

        payload = jwt_service.verify_access_token(token.token)
        assert payload is None

    def test_verify_access_token_wrong_type(self, jwt_service):
        """Test access token verification with wrong token type."""
        # Create token with wrong type
        payload = {
            "sub": str(uuid4()),
            "token_type": "refresh",  # Wrong type
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        wrong_token = jwt.encode(
            payload, jwt_service.secret_key, algorithm=jwt_service.algorithm
        )

        result = jwt_service.verify_access_token(wrong_token)
        assert result is None

    def test_verify_access_token_malformed(self, jwt_service):
        """Test access token verification with malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        payload = jwt_service.verify_access_token(malformed_token)

        assert payload is None

    def test_verify_access_token_empty_string(self, jwt_service):
        """Test access token verification with empty token."""
        payload = jwt_service.verify_access_token("")
        assert payload is None


class TestValidateAccessToken:
    """Test access token validation functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing."""
        return JWTService(secret_key="test-secret-key")

    @pytest.fixture
    def valid_token(self, jwt_service):
        """Create a valid access token for testing."""
        return jwt_service.create_access_token(
            user_id=uuid4(),
            email="validate@example.com",
            role=UserRole.TRADER,
            permissions=["read", "write"],
        )

    def test_validate_access_token_valid_returns_true(self, jwt_service, valid_token):
        """Test access token validation returns True for valid token."""
        result = jwt_service.validate_access_token(valid_token.token)
        assert result is True

    def test_validate_access_token_invalid_returns_false(self, jwt_service):
        """Test access token validation returns False for invalid token."""
        result = jwt_service.validate_access_token("invalid.token.here")
        assert result is False

    def test_validate_access_token_expired_returns_false(self, jwt_service):
        """Test access token validation returns False for expired token."""
        token = jwt_service.create_access_token(
            user_id=uuid4(),
            email="expired@example.com",
            role=UserRole.VIEWER,
            permissions=["read"],
            expires_delta=timedelta(seconds=0.001),  # Very short but not negative
        )

        # Wait a moment for token to expire
        import time

        time.sleep(0.01)

        result = jwt_service.validate_access_token(token.token)
        assert result is False

    def test_validate_access_token_wrong_secret_returns_false(
        self, jwt_service, valid_token
    ):
        """Test access token validation returns False with wrong secret."""
        different_service = JWTService(secret_key="wrong-secret")
        result = different_service.validate_access_token(valid_token.token)
        assert result is False
