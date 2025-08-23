"""Tests for AuthenticationService with comprehensive coverage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from boursa_vision.application.services.authentication_service import (
    AccountDisabledError,
    AuthenticationError,
    AuthenticationResult,
    AuthenticationService,
    InvalidCredentialsError,
    RegistrationResult,
    TokenExpiredError,
)
from boursa_vision.domain.entities.refresh_token import RefreshToken
from boursa_vision.domain.entities.user import User, UserRole
from boursa_vision.domain.events.auth_events import (
    UserLoggedOutEvent,
    UserLoginFailedEvent,
)
from boursa_vision.domain.value_objects.auth import AccessToken, TokenPair
from boursa_vision.domain.value_objects.auth import RefreshToken as RefreshTokenVO


class TestAuthenticationServiceExceptions:
    """Test authentication service custom exceptions."""

    def test_authentication_error_base_exception(self):
        """Test AuthenticationError is base exception."""
        error = AuthenticationError("Base auth error")
        assert str(error) == "Base auth error"
        assert isinstance(error, Exception)

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError inherits from AuthenticationError."""
        error = InvalidCredentialsError("Invalid creds")
        assert str(error) == "Invalid creds"
        assert isinstance(error, AuthenticationError)

    def test_account_disabled_error(self):
        """Test AccountDisabledError inherits from AuthenticationError."""
        error = AccountDisabledError("Account disabled")
        assert str(error) == "Account disabled"
        assert isinstance(error, AuthenticationError)

    def test_token_expired_error(self):
        """Test TokenExpiredError inherits from AuthenticationError."""
        error = TokenExpiredError("Token expired")
        assert str(error) == "Token expired"
        assert isinstance(error, AuthenticationError)


class TestRegistrationResult:
    """Test RegistrationResult dataclass."""

    def test_registration_result_creation(self):
        """Test RegistrationResult creation."""
        user = Mock(spec=User)
        token_pair = Mock(spec=TokenPair)

        result = RegistrationResult(user=user, token_pair=token_pair)

        assert result.user is user
        assert result.token_pair is token_pair

    def test_registration_result_frozen(self):
        """Test RegistrationResult is frozen (immutable)."""
        user = Mock(spec=User)
        token_pair = Mock(spec=TokenPair)

        result = RegistrationResult(user=user, token_pair=token_pair)

        with pytest.raises(AttributeError):
            result.user = Mock()  # Should raise error as dataclass is frozen


class TestAuthenticationResult:
    """Test AuthenticationResult dataclass."""

    def test_authentication_result_creation(self):
        """Test AuthenticationResult creation."""
        user = Mock(spec=User)
        token_pair = Mock(spec=TokenPair)

        result = AuthenticationResult(user=user, token_pair=token_pair)

        assert result.user is user
        assert result.token_pair is token_pair

    def test_authentication_result_frozen(self):
        """Test AuthenticationResult is frozen (immutable)."""
        user = Mock(spec=User)
        token_pair = Mock(spec=TokenPair)

        result = AuthenticationResult(user=user, token_pair=token_pair)

        with pytest.raises(AttributeError):
            result.token_pair = Mock()  # Should raise error as dataclass is frozen


class TestAuthenticationServiceInitialization:
    """Test AuthenticationService initialization."""

    def test_authentication_service_initialization(self):
        """Test proper initialization of AuthenticationService."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        auth_service = AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        )

        assert auth_service.user_repository is user_repo
        assert auth_service.refresh_token_repository is refresh_token_repo
        assert auth_service.password_service is password_service
        assert auth_service.jwt_service is jwt_service

    def test_authentication_service_requires_all_dependencies(self):
        """Test that AuthenticationService requires all dependencies."""
        with pytest.raises(TypeError):
            AuthenticationService()  # Missing required dependencies


class TestAuthenticateUser:
    """Test user authentication method."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return {
            "user_repo": user_repo,
            "refresh_token_repo": refresh_token_repo,
            "password_service": password_service,
            "jwt_service": jwt_service,
        }

    @pytest.fixture
    def auth_service(self, mock_dependencies):
        """Create AuthenticationService with mocked dependencies."""
        return AuthenticationService(
            user_repository=mock_dependencies["user_repo"],
            refresh_token_repository=mock_dependencies["refresh_token_repo"],
            password_service=mock_dependencies["password_service"],
            jwt_service=mock_dependencies["jwt_service"],
        )

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = uuid4()
        user.email = "test@example.com"
        user.password_hash = "hashed_password"
        user.is_active = True
        user.role = UserRole.VIEWER
        user._domain_events = []
        user._add_domain_event = Mock()
        user.update_last_login = Mock()
        return user

    @pytest.fixture
    def mock_token_pair(self):
        """Create a mock token pair."""
        access_token = Mock(spec=AccessToken)
        refresh_token = Mock(spec=RefreshTokenVO)
        refresh_token.token = "refresh_token_value"
        refresh_token.expires_at = datetime.now(UTC) + timedelta(days=7)

        token_pair = Mock(spec=TokenPair)
        token_pair.access_token = access_token
        token_pair.refresh_token = refresh_token

        return token_pair

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self, auth_service, mock_dependencies, mock_user, mock_token_pair
    ):
        """Test successful user authentication."""
        # Setup mocks
        mock_dependencies["user_repo"].find_by_email_for_auth.return_value = mock_user
        mock_dependencies["password_service"].verify_password.return_value = True
        mock_dependencies[
            "jwt_service"
        ].create_token_pair.return_value = mock_token_pair

        # Mock refresh token creation
        mock_refresh_token = Mock(spec=RefreshToken)
        with patch(
            "boursa_vision.application.services.authentication_service.RefreshTokenEntity"
        ) as MockRefreshToken:
            MockRefreshToken.create.return_value = mock_refresh_token

            # Execute
            result = await auth_service.authenticate_user(
                email="test@example.com",
                password="password123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

        # Assertions
        assert result is mock_token_pair
        mock_dependencies["user_repo"].find_by_email_for_auth.assert_called_once_with(
            "test@example.com"
        )
        mock_dependencies["password_service"].verify_password.assert_called_once_with(
            "password123", "hashed_password"
        )
        mock_user.update_last_login.assert_called_once()
        mock_dependencies["user_repo"].update.assert_called_once_with(mock_user)
        mock_dependencies["jwt_service"].create_token_pair.assert_called_once()
        mock_dependencies["refresh_token_repo"].save.assert_called_once_with(
            mock_refresh_token
        )
        mock_user._add_domain_event.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_email(
        self, auth_service, mock_dependencies
    ):
        """Test authentication with invalid email."""
        # Setup mocks
        mock_dependencies["user_repo"].find_by_email_for_auth.return_value = None

        # Execute and assert
        with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
            await auth_service.authenticate_user(
                email="nonexistent@example.com", password="password123"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(
        self, auth_service, mock_dependencies, mock_user
    ):
        """Test authentication with invalid password."""
        # Setup mocks
        mock_dependencies["user_repo"].find_by_email_for_auth.return_value = mock_user
        mock_dependencies["password_service"].verify_password.return_value = False

        # Execute and assert
        with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
            await auth_service.authenticate_user(
                email="test@example.com", password="wrong_password"
            )

        # Verify failed login event was added
        mock_user._add_domain_event.assert_called()
        call_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(call_args, UserLoginFailedEvent)
        assert call_args.failure_reason == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_authenticate_user_disabled_account(
        self, auth_service, mock_dependencies, mock_user
    ):
        """Test authentication with disabled account."""
        # Setup mocks
        mock_user.is_active = False
        mock_dependencies["user_repo"].find_by_email_for_auth.return_value = mock_user
        mock_dependencies["password_service"].verify_password.return_value = True

        # Execute and assert
        with pytest.raises(AccountDisabledError, match="Account is disabled"):
            await auth_service.authenticate_user(
                email="test@example.com", password="password123"
            )

        # Verify failed login event was added
        mock_user._add_domain_event.assert_called()
        call_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(call_args, UserLoginFailedEvent)
        assert call_args.failure_reason == "account_disabled"

    @pytest.mark.asyncio
    async def test_authenticate_user_with_optional_parameters(
        self, auth_service, mock_dependencies, mock_user, mock_token_pair
    ):
        """Test authentication with optional IP and user agent parameters."""
        # Setup mocks
        mock_dependencies["user_repo"].find_by_email_for_auth.return_value = mock_user
        mock_dependencies["password_service"].verify_password.return_value = True
        mock_dependencies[
            "jwt_service"
        ].create_token_pair.return_value = mock_token_pair

        mock_refresh_token = Mock(spec=RefreshToken)
        with patch(
            "boursa_vision.application.services.authentication_service.RefreshTokenEntity"
        ) as MockRefreshToken:
            MockRefreshToken.create.return_value = mock_refresh_token

            # Execute with default parameters
            result = await auth_service.authenticate_user(
                email="test@example.com", password="password123"
            )

        assert result is mock_token_pair

        # Verify RefreshToken was created with default parameters
        MockRefreshToken.create.assert_called_once()
        call_kwargs = MockRefreshToken.create.call_args.kwargs
        assert call_kwargs["ip_address"] == ""
        assert call_kwargs["user_agent"] == ""


class TestRefreshAccessToken:
    """Test refresh access token method."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create AuthenticationService with mocked dependencies."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        ), {
            "user_repo": user_repo,
            "refresh_token_repo": refresh_token_repo,
            "jwt_service": jwt_service,
        }

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, auth_service_with_mocks):
        """Test successful access token refresh."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.user_id = uuid4()
        mock_token_entity.is_valid.return_value = True
        mock_token_entity.use = Mock()

        mock_user = Mock(spec=User)
        mock_user.id = mock_token_entity.user_id
        mock_user.email = "test@example.com"
        mock_user.role = UserRole.VIEWER
        mock_user.is_active = True

        mock_new_token_pair = Mock(spec=TokenPair)
        mock_new_token_pair.refresh_token = Mock()
        mock_new_token_pair.refresh_token.token = "new_refresh_token"
        mock_new_token_pair.refresh_token.expires_at = datetime.now(UTC) + timedelta(
            days=7
        )

        mocks["refresh_token_repo"].find_by_token.return_value = mock_token_entity
        mocks["user_repo"].find_by_id.return_value = mock_user
        mocks["jwt_service"].create_token_pair.return_value = mock_new_token_pair

        # Execute
        result = await auth_service.refresh_access_token("refresh_token")

        # Assertions
        assert result is mock_new_token_pair
        mocks["refresh_token_repo"].find_by_token.assert_called_once_with(
            "refresh_token"
        )
        mock_token_entity.is_valid.assert_called_once()
        mocks["user_repo"].find_by_id.assert_called_once_with(mock_token_entity.user_id)
        mock_token_entity.use.assert_called_once()
        mocks["jwt_service"].create_token_pair.assert_called_once()
        mocks["refresh_token_repo"].update.assert_called_once_with(mock_token_entity)

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_token(self, auth_service_with_mocks):
        """Test refresh with invalid token."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mocks["refresh_token_repo"].find_by_token.return_value = None

        # Execute and assert
        with pytest.raises(TokenExpiredError, match="Invalid or expired refresh token"):
            await auth_service.refresh_access_token("invalid_token")

    @pytest.mark.asyncio
    async def test_refresh_access_token_expired_token(self, auth_service_with_mocks):
        """Test refresh with expired token."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.is_valid.return_value = False
        mocks["refresh_token_repo"].find_by_token.return_value = mock_token_entity

        # Execute and assert
        with pytest.raises(TokenExpiredError, match="Invalid or expired refresh token"):
            await auth_service.refresh_access_token("expired_token")

    @pytest.mark.asyncio
    async def test_refresh_access_token_user_not_found(self, auth_service_with_mocks):
        """Test refresh when user is not found."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.user_id = uuid4()
        mock_token_entity.is_valid.return_value = True

        mocks["refresh_token_repo"].find_by_token.return_value = mock_token_entity
        mocks["user_repo"].find_by_id.return_value = None

        # Execute and assert
        with pytest.raises(TokenExpiredError, match="User not found or inactive"):
            await auth_service.refresh_access_token("refresh_token")

    @pytest.mark.asyncio
    async def test_refresh_access_token_inactive_user(self, auth_service_with_mocks):
        """Test refresh when user is inactive."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.user_id = uuid4()
        mock_token_entity.is_valid.return_value = True

        mock_user = Mock(spec=User)
        mock_user.is_active = False

        mocks["refresh_token_repo"].find_by_token.return_value = mock_token_entity
        mocks["user_repo"].find_by_id.return_value = mock_user

        # Execute and assert
        with pytest.raises(TokenExpiredError, match="User not found or inactive"):
            await auth_service.refresh_access_token("refresh_token")


class TestLogoutUser:
    """Test user logout method."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create AuthenticationService with mocked dependencies."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        ), {
            "user_repo": user_repo,
            "refresh_token_repo": refresh_token_repo,
        }

    @pytest.mark.asyncio
    async def test_logout_user_single_session(self, auth_service_with_mocks):
        """Test logout of single session."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user._add_domain_event = Mock()

        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.revoke = Mock()

        mocks["user_repo"].find_by_id.return_value = mock_user
        mocks["refresh_token_repo"].find_by_token.return_value = mock_token_entity

        # Execute
        await auth_service.logout_user(user_id=user_id, refresh_token="refresh_token")

        # Assertions
        mocks["user_repo"].find_by_id.assert_called_once_with(user_id)
        mocks["refresh_token_repo"].find_by_token.assert_called_once_with(
            "refresh_token"
        )
        mock_token_entity.revoke.assert_called_once_with("manual_logout")
        mocks["refresh_token_repo"].update.assert_called_once_with(mock_token_entity)

        # Check logout event was added
        mock_user._add_domain_event.assert_called()
        call_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(call_args, UserLoggedOutEvent)
        assert call_args.logout_method == "manual"

    @pytest.mark.asyncio
    async def test_logout_user_all_sessions(self, auth_service_with_mocks):
        """Test logout of all sessions."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user._add_domain_event = Mock()

        mocks["user_repo"].find_by_id.return_value = mock_user

        # Execute
        await auth_service.logout_user(user_id=user_id, logout_all_sessions=True)

        # Assertions
        mocks["refresh_token_repo"].revoke_all_for_user.assert_called_once_with(
            user_id, reason="logout_all"
        )

        # Check logout event was added
        mock_user._add_domain_event.assert_called()
        call_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(call_args, UserLoggedOutEvent)
        assert call_args.logout_method == "logout_all"

    @pytest.mark.asyncio
    async def test_logout_user_not_found(self, auth_service_with_mocks):
        """Test logout when user is not found."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mocks["user_repo"].find_by_id.return_value = None

        # Execute (should not raise exception)
        await auth_service.logout_user(user_id=user_id)

        # Verify no further operations were attempted
        mocks["refresh_token_repo"].find_by_token.assert_not_called()
        mocks["refresh_token_repo"].revoke_all_for_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_logout_user_refresh_token_not_found(self, auth_service_with_mocks):
        """Test logout when refresh token is not found."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user._add_domain_event = Mock()

        mocks["user_repo"].find_by_id.return_value = mock_user
        mocks["refresh_token_repo"].find_by_token.return_value = None

        # Execute
        await auth_service.logout_user(
            user_id=user_id, refresh_token="nonexistent_token"
        )

        # Should still add logout event
        mock_user._add_domain_event.assert_called()
        mocks["refresh_token_repo"].update.assert_not_called()


class TestValidateAccessToken:
    """Test access token validation method."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create AuthenticationService with mocked dependencies."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        ), {
            "user_repo": user_repo,
            "jwt_service": jwt_service,
        }

    @pytest.mark.asyncio
    async def test_validate_access_token_success(self, auth_service_with_mocks):
        """Test successful access token validation."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_payload = {"sub": str(user_id), "email": "test@example.com"}
        mock_user = Mock(spec=User)
        mock_user.is_active = True

        mocks["jwt_service"].verify_access_token.return_value = mock_payload
        mocks["user_repo"].find_by_id.return_value = mock_user

        # Execute
        result = await auth_service.validate_access_token("valid_token")

        # Assertions
        assert result is mock_user
        mocks["jwt_service"].verify_access_token.assert_called_once_with("valid_token")
        mocks["user_repo"].find_by_id.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_validate_access_token_invalid_jwt(self, auth_service_with_mocks):
        """Test validation with invalid JWT token."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mocks["jwt_service"].verify_access_token.return_value = None

        # Execute
        result = await auth_service.validate_access_token("invalid_token")

        # Assertions
        assert result is None
        mocks["user_repo"].find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_access_token_no_subject(self, auth_service_with_mocks):
        """Test validation with token missing subject."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mock_payload = {"email": "test@example.com"}  # Missing 'sub'
        mocks["jwt_service"].verify_access_token.return_value = mock_payload

        # Execute
        result = await auth_service.validate_access_token("token_without_sub")

        # Assertions
        assert result is None
        mocks["user_repo"].find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_access_token_invalid_uuid(self, auth_service_with_mocks):
        """Test validation with invalid UUID in subject."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mock_payload = {"sub": "invalid-uuid", "email": "test@example.com"}
        mocks["jwt_service"].verify_access_token.return_value = mock_payload

        # Execute
        result = await auth_service.validate_access_token("token_with_invalid_uuid")

        # Assertions
        assert result is None
        mocks["user_repo"].find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_access_token_user_not_found(self, auth_service_with_mocks):
        """Test validation when user is not found."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_payload = {"sub": str(user_id), "email": "test@example.com"}
        mocks["jwt_service"].verify_access_token.return_value = mock_payload
        mocks["user_repo"].find_by_id.return_value = None

        # Execute
        result = await auth_service.validate_access_token("token_for_missing_user")

        # Assertions
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_access_token_inactive_user(self, auth_service_with_mocks):
        """Test validation when user is inactive."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_payload = {"sub": str(user_id), "email": "test@example.com"}
        mock_user = Mock(spec=User)
        mock_user.is_active = False

        mocks["jwt_service"].verify_access_token.return_value = mock_payload
        mocks["user_repo"].find_by_id.return_value = mock_user

        # Execute
        result = await auth_service.validate_access_token("token_for_inactive_user")

        # Assertions
        assert result is None


class TestRegisterUser:
    """Test user registration method."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create AuthenticationService with mocked dependencies."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        ), {
            "user_repo": user_repo,
            "password_service": password_service,
            "jwt_service": jwt_service,
        }

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service_with_mocks):
        """Test successful user registration."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mocks["user_repo"].exists_by_email.return_value = False
        mocks["user_repo"].exists_by_username.return_value = False
        mocks["password_service"].hash_password.return_value = "hashed_password"

        # Setup mocks
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()  # Add the missing id attribute
        mock_token_pair = Mock(spec=TokenPair)

        with patch(
            "boursa_vision.application.services.authentication_service.User"
        ) as MockUser:
            MockUser.create.return_value = mock_user
            mocks["jwt_service"].create_token_pair.return_value = mock_token_pair

            # Execute
            result = await auth_service.register_user(
                email="test@example.com",
                username="testuser",
                password="password123",
                first_name="John",
                last_name="Doe",
            )

        # Assertions
        assert isinstance(result, RegistrationResult)
        assert result.user is mock_user
        assert result.token_pair is mock_token_pair

        mocks["user_repo"].exists_by_email.assert_called_once_with("test@example.com")
        mocks["user_repo"].exists_by_username.assert_called_once_with("testuser")
        mocks["password_service"].hash_password.assert_called_once_with("password123")
        MockUser.create.assert_called_once()
        mocks["user_repo"].save.assert_called_once_with(mock_user)
        mocks["jwt_service"].create_token_pair.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, auth_service_with_mocks):
        """Test registration when email already exists."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mocks["user_repo"].exists_by_email.return_value = True

        # Execute and assert
        with pytest.raises(ValueError, match="User with this email already exists"):
            await auth_service.register_user(
                email="existing@example.com",
                username="testuser",
                password="password123",
                first_name="John",
                last_name="Doe",
            )

    @pytest.mark.asyncio
    async def test_register_user_username_exists(self, auth_service_with_mocks):
        """Test registration when username already exists."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mocks["user_repo"].exists_by_email.return_value = False
        mocks["user_repo"].exists_by_username.return_value = True

        # Execute and assert
        with pytest.raises(ValueError, match="User with this username already exists"):
            await auth_service.register_user(
                email="test@example.com",
                username="existing_user",
                password="password123",
                first_name="John",
                last_name="Doe",
            )


class TestChangePassword:
    """Test change password method."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create AuthenticationService with mocked dependencies."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        ), {
            "user_repo": user_repo,
            "password_service": password_service,
        }

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service_with_mocks):
        """Test successful password change."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_user = Mock(spec=User)
        mock_user.password_hash = "old_hashed_password"

        mocks["user_repo"].find_by_id.return_value = mock_user
        mocks["password_service"].verify_password.return_value = True
        mocks["password_service"].hash_password.return_value = "new_hashed_password"

        # Execute
        result = await auth_service.change_password(
            user_id=user_id, old_password="old_password", new_password="new_password"
        )

        # Assertions
        assert result is True
        mocks["user_repo"].find_by_id.assert_called_once_with(user_id)
        mocks["password_service"].verify_password.assert_called_once_with(
            "old_password", "old_hashed_password"
        )
        mocks["password_service"].hash_password.assert_called_once_with("new_password")
        assert mock_user.password_hash == "new_hashed_password"
        mocks["user_repo"].save.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, auth_service_with_mocks):
        """Test password change when user is not found."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mocks["user_repo"].find_by_id.return_value = None

        # Execute and assert
        with pytest.raises(ValueError, match="User not found"):
            await auth_service.change_password(
                user_id=user_id,
                old_password="old_password",
                new_password="new_password",
            )

    @pytest.mark.asyncio
    async def test_change_password_incorrect_old_password(
        self, auth_service_with_mocks
    ):
        """Test password change with incorrect old password."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        user_id = uuid4()
        mock_user = Mock(spec=User)
        mock_user.password_hash = "old_hashed_password"

        mocks["user_repo"].find_by_id.return_value = mock_user
        mocks["password_service"].verify_password.return_value = False

        # Execute and assert
        with pytest.raises(ValueError, match="Incorrect old password"):
            await auth_service.change_password(
                user_id=user_id,
                old_password="wrong_password",
                new_password="new_password",
            )


class TestCleanupExpiredTokens:
    """Test cleanup expired tokens method."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create AuthenticationService with mocked dependencies."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        ), {
            "refresh_token_repo": refresh_token_repo,
        }

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_success(self, auth_service_with_mocks):
        """Test successful cleanup of expired tokens."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mocks["refresh_token_repo"].cleanup_expired_tokens.return_value = 5

        with patch("datetime.datetime") as mock_datetime:
            mock_now = datetime.now(UTC)
            mock_datetime.now.return_value = mock_now

            # Execute
            result = await auth_service.cleanup_expired_tokens()

        # Assertions
        assert result == 5
        mocks["refresh_token_repo"].cleanup_expired_tokens.assert_called_once_with(
            mock_now
        )

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_no_tokens(self, auth_service_with_mocks):
        """Test cleanup when no tokens are expired."""
        auth_service, mocks = auth_service_with_mocks

        # Setup mocks
        mocks["refresh_token_repo"].cleanup_expired_tokens.return_value = 0

        # Execute
        result = await auth_service.cleanup_expired_tokens()

        # Assertions
        assert result == 0


class TestAuthenticationServiceIntegration:
    """Integration tests for AuthenticationService."""

    @pytest.fixture
    def full_auth_service_mock(self):
        """Create fully mocked AuthenticationService for integration tests."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        auth_service = AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        )

        return auth_service, {
            "user_repo": user_repo,
            "refresh_token_repo": refresh_token_repo,
            "password_service": password_service,
            "jwt_service": jwt_service,
        }

    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self, full_auth_service_mock):
        """Test complete authentication flow from login to logout."""
        auth_service, mocks = full_auth_service_mock

        # Setup user and mocks
        user_id = uuid4()
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.password_hash = "hashed_password"
        mock_user.is_active = True
        mock_user.role = UserRole.VIEWER
        mock_user._domain_events = []
        mock_user._add_domain_event = Mock()
        mock_user.update_last_login = Mock()

        mock_token_pair = Mock(spec=TokenPair)
        mock_token_pair.refresh_token = Mock()
        mock_token_pair.refresh_token.token = "refresh_token_value"
        mock_token_pair.refresh_token.expires_at = datetime.now(UTC) + timedelta(days=7)

        # Setup all mocks
        mocks["user_repo"].find_by_email_for_auth.return_value = mock_user
        mocks["password_service"].verify_password.return_value = True
        mocks["jwt_service"].create_token_pair.return_value = mock_token_pair
        mocks["user_repo"].find_by_id.return_value = mock_user

        mock_refresh_token = Mock(spec=RefreshToken)

        # 1. Test login
        with patch(
            "boursa_vision.application.services.authentication_service.RefreshTokenEntity"
        ) as MockRefreshToken:
            MockRefreshToken.create.return_value = mock_refresh_token

            login_result = await auth_service.authenticate_user(
                email="test@example.com",
                password="password123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

        assert login_result is mock_token_pair

        # 2. Test token validation
        mock_payload = {"sub": str(user_id), "email": "test@example.com"}
        mocks["jwt_service"].verify_access_token.return_value = mock_payload

        validated_user = await auth_service.validate_access_token("access_token")
        assert validated_user is mock_user

        # 3. Test logout
        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.revoke = Mock()
        mocks["refresh_token_repo"].find_by_token.return_value = mock_token_entity

        await auth_service.logout_user(
            user_id=user_id, refresh_token="refresh_token_value"
        )

        # Verify complete flow
        assert mock_user._add_domain_event.call_count >= 2  # Login and logout events
        mock_token_entity.revoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_security_event_logging(self, full_auth_service_mock):
        """Test that security events are properly logged."""
        auth_service, mocks = full_auth_service_mock

        # Setup for failed login
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.password_hash = "hashed_password"
        mock_user._add_domain_event = Mock()

        mocks["user_repo"].find_by_email_for_auth.return_value = mock_user
        mocks["password_service"].verify_password.return_value = False

        # Test failed login event
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(
                email="test@example.com",
                password="wrong_password",
                ip_address="192.168.1.100",
                user_agent="Evil Browser",
            )

        # Verify security event was logged
        mock_user._add_domain_event.assert_called()
        call_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(call_args, UserLoginFailedEvent)
        assert call_args.ip_address == "192.168.1.100"
        assert call_args.user_agent == "Evil Browser"
        assert call_args.failure_reason == "invalid_credentials"
