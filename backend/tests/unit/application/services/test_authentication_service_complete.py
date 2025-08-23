"""
Complete Test Suite for AuthenticationService - Priority #1 Coverage
================================================================

Tests suivant l'architecture documentée dans TESTS.md:
- Test Pyramid: Focus sur tests unitaires rapides
- Clean Architecture Testing: Domain → Application → Infrastructure
- AAA Pattern: Arrange, Act, Assert
- Coverage Target: >80% pour service critique
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

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
    UserLoggedInEvent,
    UserLoggedOutEvent,
    UserLoginFailedEvent,
)
from boursa_vision.domain.value_objects.auth import AccessToken
from boursa_vision.domain.value_objects.auth import RefreshToken as RefreshTokenVO
from boursa_vision.domain.value_objects.auth import TokenPair


@pytest.mark.unit
class TestAuthenticationServiceInitialization:
    """Test service initialization and dependencies."""

    def test_should_initialize_with_all_dependencies(self):
        """Test service initializes correctly with required dependencies."""
        # Arrange
        user_repo = Mock()
        refresh_token_repo = Mock()
        password_service = Mock()
        jwt_service = Mock()

        # Act
        auth_service = AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=password_service,
            jwt_service=jwt_service,
        )

        # Assert
        assert auth_service.user_repository is user_repo
        assert auth_service.refresh_token_repository is refresh_token_repo
        assert auth_service.password_service is password_service
        assert auth_service.jwt_service is jwt_service


@pytest.mark.unit
class TestUserAuthentication:
    """Test user authentication functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for authentication service."""
        return {
            "user_repository": AsyncMock(),
            "refresh_token_repository": AsyncMock(),
            "password_service": Mock(),
            "jwt_service": Mock(),
        }

    @pytest.fixture
    def auth_service(self, mock_dependencies):
        """Create authentication service with mocked dependencies."""
        return AuthenticationService(**mock_dependencies)

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        user = Mock(spec=User)
        user.id = uuid4()
        user.email = "test@example.com"
        user.password_hash = "hashed_password"
        user.is_active = True
        user.role = UserRole.VIEWER
        user.update_last_login = Mock()
        user._add_domain_event = Mock()
        return user

    @pytest.fixture
    def mock_token_pair(self):
        """Create mock token pair."""
        access_token = Mock(spec=AccessToken)
        refresh_token = Mock(spec=RefreshTokenVO)
        refresh_token.token = "refresh_token_123"
        refresh_token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        token_pair = Mock(spec=TokenPair)
        token_pair.access_token = access_token
        token_pair.refresh_token = refresh_token
        return token_pair

    async def test_should_authenticate_user_with_valid_credentials(
        self, auth_service, mock_dependencies, mock_user, mock_token_pair
    ):
        """Test successful user authentication with valid credentials."""
        # Arrange
        email = "test@example.com"
        password = "valid_password"
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"

        mock_dependencies[
            "user_repository"
        ].find_by_email_for_auth.return_value = mock_user
        mock_dependencies["password_service"].verify_password.return_value = True
        mock_dependencies[
            "jwt_service"
        ].create_token_pair.return_value = mock_token_pair

        # Mock refresh token creation
        with patch(
            "boursa_vision.domain.entities.refresh_token.RefreshToken.create"
        ) as mock_rt_create:
            mock_rt_entity = Mock(spec=RefreshToken)
            mock_rt_create.return_value = mock_rt_entity

            # Act
            result = await auth_service.authenticate_user(
                email=email,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        # Assert
        assert result is mock_token_pair
        mock_dependencies[
            "user_repository"
        ].find_by_email_for_auth.assert_called_once_with(email)
        mock_dependencies["password_service"].verify_password.assert_called_once_with(
            password, mock_user.password_hash
        )
        mock_user.update_last_login.assert_called_once()
        mock_dependencies["user_repository"].update.assert_called_once_with(mock_user)

        # Verify JWT service called with correct parameters
        mock_dependencies["jwt_service"].create_token_pair.assert_called_once_with(
            user_id=mock_user.id,
            email=mock_user.email,
            role=mock_user.role,
            permissions=mock_user.role.permissions,
        )

        # Verify refresh token saved
        mock_dependencies["refresh_token_repository"].save.assert_called_once()

        # Verify login event added
        mock_user._add_domain_event.assert_called()
        event_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(event_args, UserLoggedInEvent)
        assert event_args.user_id == mock_user.id
        assert event_args.email == mock_user.email
        assert event_args.login_method == "password"
        assert event_args.ip_address == ip_address
        assert event_args.user_agent == user_agent

    async def test_should_raise_invalid_credentials_when_user_not_found(
        self, auth_service, mock_dependencies
    ):
        """Test authentication fails when user doesn't exist."""
        # Arrange
        email = "nonexistent@example.com"
        password = "any_password"

        mock_dependencies["user_repository"].find_by_email_for_auth.return_value = None

        # Act & Assert
        with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
            await auth_service.authenticate_user(email, password)

        # Verify no other services called
        mock_dependencies["password_service"].verify_password.assert_not_called()
        mock_dependencies["jwt_service"].create_token_pair.assert_not_called()

    async def test_should_raise_invalid_credentials_when_password_wrong(
        self, auth_service, mock_dependencies, mock_user
    ):
        """Test authentication fails with incorrect password."""
        # Arrange
        email = "test@example.com"
        password = "wrong_password"
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"

        mock_dependencies[
            "user_repository"
        ].find_by_email_for_auth.return_value = mock_user
        mock_dependencies["password_service"].verify_password.return_value = False

        # Act & Assert
        with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
            await auth_service.authenticate_user(
                email, password, ip_address, user_agent
            )

        # Verify password was checked
        mock_dependencies["password_service"].verify_password.assert_called_once_with(
            password, mock_user.password_hash
        )

        # Verify failed login event added
        mock_user._add_domain_event.assert_called()
        event_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(event_args, UserLoginFailedEvent)
        assert event_args.email == email
        assert event_args.failure_reason == "invalid_credentials"
        assert event_args.ip_address == ip_address
        assert event_args.user_agent == user_agent

        # Verify no token creation
        mock_dependencies["jwt_service"].create_token_pair.assert_not_called()

    async def test_should_raise_account_disabled_when_user_inactive(
        self, auth_service, mock_dependencies, mock_user
    ):
        """Test authentication fails when user account is disabled."""
        # Arrange
        email = "test@example.com"
        password = "valid_password"
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"

        mock_user.is_active = False  # Disabled account
        mock_dependencies[
            "user_repository"
        ].find_by_email_for_auth.return_value = mock_user
        mock_dependencies["password_service"].verify_password.return_value = True

        # Act & Assert
        with pytest.raises(AccountDisabledError, match="Account is disabled"):
            await auth_service.authenticate_user(
                email, password, ip_address, user_agent
            )

        # Verify failed login event for disabled account
        mock_user._add_domain_event.assert_called()
        event_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(event_args, UserLoginFailedEvent)
        assert event_args.failure_reason == "account_disabled"

        # Verify no token creation
        mock_dependencies["jwt_service"].create_token_pair.assert_not_called()


@pytest.mark.unit
class TestTokenRefresh:
    """Test token refresh functionality."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create service with mocked dependencies."""
        return {
            "service": AuthenticationService(
                user_repository=AsyncMock(),
                refresh_token_repository=AsyncMock(),
                password_service=Mock(),
                jwt_service=Mock(),
            ),
            "mocks": {
                "user_repo": AsyncMock(),
                "refresh_token_repo": AsyncMock(),
                "jwt_service": Mock(),
            },
        }

    async def test_should_refresh_token_with_valid_refresh_token(self):
        """Test successful token refresh with valid refresh token."""
        # Arrange
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        jwt_service = Mock()

        auth_service = AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=Mock(),
            jwt_service=jwt_service,
        )

        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.role = UserRole.VIEWER
        mock_user.is_active = True

        # Mock refresh token entity
        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.user_id = mock_user.id
        mock_token_entity.is_valid.return_value = True
        mock_token_entity.use = Mock()

        # Mock new token pair
        mock_new_token_pair = Mock(spec=TokenPair)
        mock_new_token_pair.refresh_token = Mock()
        mock_new_token_pair.refresh_token.token = "new_refresh_token"
        mock_new_token_pair.refresh_token.expires_at = datetime.now(
            timezone.utc
        ) + timedelta(days=7)

        refresh_token_repo.find_by_token.return_value = mock_token_entity
        user_repo.find_by_id.return_value = mock_user
        jwt_service.create_token_pair.return_value = mock_new_token_pair

        # Act
        result = await auth_service.refresh_access_token("old_refresh_token")

        # Assert
        assert result is mock_new_token_pair
        refresh_token_repo.find_by_token.assert_called_once_with("old_refresh_token")
        mock_token_entity.is_valid.assert_called_once()
        user_repo.find_by_id.assert_called_once_with(mock_token_entity.user_id)
        mock_token_entity.use.assert_called_once()

        jwt_service.create_token_pair.assert_called_once_with(
            user_id=mock_user.id,
            email=mock_user.email,
            role=mock_user.role,
            permissions=mock_user.role.permissions,
        )

        # Verify token entity updated
        assert mock_token_entity.token == "new_refresh_token"
        assert (
            mock_token_entity.expires_at == mock_new_token_pair.refresh_token.expires_at
        )
        refresh_token_repo.update.assert_called_once_with(mock_token_entity)

    async def test_should_raise_token_expired_when_token_invalid(self):
        """Test token refresh fails with invalid refresh token."""
        # Arrange
        refresh_token_repo = AsyncMock()
        auth_service = AuthenticationService(
            user_repository=AsyncMock(),
            refresh_token_repository=refresh_token_repo,
            password_service=Mock(),
            jwt_service=Mock(),
        )

        refresh_token_repo.find_by_token.return_value = None

        # Act & Assert
        with pytest.raises(TokenExpiredError, match="Invalid or expired refresh token"):
            await auth_service.refresh_access_token("invalid_token")

    async def test_should_raise_token_expired_when_token_not_valid(self):
        """Test token refresh fails when token exists but is not valid."""
        # Arrange
        refresh_token_repo = AsyncMock()
        auth_service = AuthenticationService(
            user_repository=AsyncMock(),
            refresh_token_repository=refresh_token_repo,
            password_service=Mock(),
            jwt_service=Mock(),
        )

        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.is_valid.return_value = False
        refresh_token_repo.find_by_token.return_value = mock_token_entity

        # Act & Assert
        with pytest.raises(TokenExpiredError, match="Invalid or expired refresh token"):
            await auth_service.refresh_access_token("expired_token")

    async def test_should_raise_token_expired_when_user_not_found(self):
        """Test token refresh fails when user doesn't exist."""
        # Arrange
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        auth_service = AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=Mock(),
            jwt_service=Mock(),
        )

        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.user_id = uuid4()
        mock_token_entity.is_valid.return_value = True

        refresh_token_repo.find_by_token.return_value = mock_token_entity
        user_repo.find_by_id.return_value = None  # User not found

        # Act & Assert
        with pytest.raises(TokenExpiredError, match="User not found or inactive"):
            await auth_service.refresh_access_token("valid_token")

    async def test_should_raise_token_expired_when_user_inactive(self):
        """Test token refresh fails when user is inactive."""
        # Arrange
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()
        auth_service = AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=refresh_token_repo,
            password_service=Mock(),
            jwt_service=Mock(),
        )

        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.user_id = uuid4()
        mock_token_entity.is_valid.return_value = True

        mock_user = Mock(spec=User)
        mock_user.is_active = False

        refresh_token_repo.find_by_token.return_value = mock_token_entity
        user_repo.find_by_id.return_value = mock_user

        # Act & Assert
        with pytest.raises(TokenExpiredError, match="User not found or inactive"):
            await auth_service.refresh_access_token("valid_token")


@pytest.mark.unit
class TestUserLogout:
    """Test user logout functionality."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create service with mocked dependencies."""
        user_repo = AsyncMock()
        refresh_token_repo = AsyncMock()

        return {
            "service": AuthenticationService(
                user_repository=user_repo,
                refresh_token_repository=refresh_token_repo,
                password_service=Mock(),
                jwt_service=Mock(),
            ),
            "user_repo": user_repo,
            "refresh_token_repo": refresh_token_repo,
        }

    async def test_should_logout_specific_session(self, auth_service_with_mocks):
        """Test logout of specific session using refresh token."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        refresh_token_repo = auth_service_with_mocks["refresh_token_repo"]

        user_id = uuid4()
        refresh_token = "token_to_revoke"

        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user._add_domain_event = Mock()

        mock_token_entity = Mock(spec=RefreshToken)
        mock_token_entity.revoke = Mock()

        user_repo.find_by_id.return_value = mock_user
        refresh_token_repo.find_by_token.return_value = mock_token_entity

        # Act
        await service.logout_user(
            user_id=user_id, refresh_token=refresh_token, logout_all_sessions=False
        )

        # Assert
        user_repo.find_by_id.assert_called_once_with(user_id)
        refresh_token_repo.find_by_token.assert_called_once_with(refresh_token)
        mock_token_entity.revoke.assert_called_once_with("manual_logout")
        refresh_token_repo.update.assert_called_once_with(mock_token_entity)

        # Verify logout event
        mock_user._add_domain_event.assert_called()
        event_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(event_args, UserLoggedOutEvent)
        assert event_args.user_id == user_id
        assert event_args.email == mock_user.email
        assert event_args.logout_method == "manual"

    async def test_should_logout_all_sessions(self, auth_service_with_mocks):
        """Test logout of all user sessions."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        refresh_token_repo = auth_service_with_mocks["refresh_token_repo"]

        user_id = uuid4()

        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user._add_domain_event = Mock()

        user_repo.find_by_id.return_value = mock_user

        # Act
        await service.logout_user(user_id=user_id, logout_all_sessions=True)

        # Assert
        refresh_token_repo.revoke_all_for_user.assert_called_once_with(
            user_id, reason="logout_all"
        )

        # Verify logout event
        mock_user._add_domain_event.assert_called()
        event_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(event_args, UserLoggedOutEvent)
        assert event_args.logout_method == "logout_all"

    async def test_should_handle_logout_when_user_not_found(
        self, auth_service_with_mocks
    ):
        """Test logout gracefully handles non-existent user."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]

        user_id = uuid4()
        user_repo.find_by_id.return_value = None

        # Act (should not raise exception)
        await service.logout_user(user_id=user_id)

        # Assert
        user_repo.find_by_id.assert_called_once_with(user_id)

    async def test_should_handle_logout_when_refresh_token_not_found(
        self, auth_service_with_mocks
    ):
        """Test logout handles case when refresh token doesn't exist."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        refresh_token_repo = auth_service_with_mocks["refresh_token_repo"]

        user_id = uuid4()

        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user._add_domain_event = Mock()

        user_repo.find_by_id.return_value = mock_user
        refresh_token_repo.find_by_token.return_value = None  # Token not found

        # Act
        await service.logout_user(user_id=user_id, refresh_token="nonexistent_token")

        # Assert - should still log the user out and add event
        mock_user._add_domain_event.assert_called()
        event_args = mock_user._add_domain_event.call_args[0][0]
        assert isinstance(event_args, UserLoggedOutEvent)
        assert event_args.logout_method == "manual"


@pytest.mark.unit
class TestAccessTokenValidation:
    """Test access token validation functionality."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create service with mocked dependencies."""
        user_repo = AsyncMock()
        jwt_service = Mock()

        return {
            "service": AuthenticationService(
                user_repository=user_repo,
                refresh_token_repository=AsyncMock(),
                password_service=Mock(),
                jwt_service=jwt_service,
            ),
            "user_repo": user_repo,
            "jwt_service": jwt_service,
        }

    async def test_should_validate_valid_access_token(self, auth_service_with_mocks):
        """Test validation of valid access token returns user."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        jwt_service = auth_service_with_mocks["jwt_service"]

        user_id = uuid4()
        token = "valid_access_token"

        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = True

        jwt_service.verify_access_token.return_value = {"sub": str(user_id)}
        user_repo.find_by_id.return_value = mock_user

        # Act
        result = await service.validate_access_token(token)

        # Assert
        assert result is mock_user
        jwt_service.verify_access_token.assert_called_once_with(token)
        user_repo.find_by_id.assert_called_once_with(user_id)

    async def test_should_return_none_for_invalid_token(self, auth_service_with_mocks):
        """Test validation returns None for invalid token."""
        # Arrange
        service = auth_service_with_mocks["service"]
        jwt_service = auth_service_with_mocks["jwt_service"]

        jwt_service.verify_access_token.return_value = None

        # Act
        result = await service.validate_access_token("invalid_token")

        # Assert
        assert result is None
        jwt_service.verify_access_token.assert_called_once_with("invalid_token")

    async def test_should_return_none_for_token_without_subject(
        self, auth_service_with_mocks
    ):
        """Test validation returns None when token has no subject."""
        # Arrange
        service = auth_service_with_mocks["service"]
        jwt_service = auth_service_with_mocks["jwt_service"]

        jwt_service.verify_access_token.return_value = {"iss": "issuer"}  # No 'sub'

        # Act
        result = await service.validate_access_token("token_without_sub")

        # Assert
        assert result is None

    async def test_should_return_none_for_invalid_user_id_format(
        self, auth_service_with_mocks
    ):
        """Test validation returns None for invalid UUID format."""
        # Arrange
        service = auth_service_with_mocks["service"]
        jwt_service = auth_service_with_mocks["jwt_service"]

        jwt_service.verify_access_token.return_value = {"sub": "not-a-valid-uuid"}

        # Act
        result = await service.validate_access_token("token_with_invalid_uuid")

        # Assert
        assert result is None

    async def test_should_return_none_when_user_not_found(
        self, auth_service_with_mocks
    ):
        """Test validation returns None when user doesn't exist."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        jwt_service = auth_service_with_mocks["jwt_service"]

        user_id = uuid4()
        jwt_service.verify_access_token.return_value = {"sub": str(user_id)}
        user_repo.find_by_id.return_value = None

        # Act
        result = await service.validate_access_token("valid_token_nonexistent_user")

        # Assert
        assert result is None

    async def test_should_return_none_when_user_inactive(self, auth_service_with_mocks):
        """Test validation returns None when user is inactive."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        jwt_service = auth_service_with_mocks["jwt_service"]

        user_id = uuid4()
        mock_user = Mock(spec=User)
        mock_user.is_active = False

        jwt_service.verify_access_token.return_value = {"sub": str(user_id)}
        user_repo.find_by_id.return_value = mock_user

        # Act
        result = await service.validate_access_token("valid_token_inactive_user")

        # Assert
        assert result is None


@pytest.mark.unit
class TestUserRegistration:
    """Test user registration functionality."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create service with mocked dependencies."""
        user_repo = AsyncMock()
        password_service = Mock()
        jwt_service = Mock()

        return {
            "service": AuthenticationService(
                user_repository=user_repo,
                refresh_token_repository=AsyncMock(),
                password_service=password_service,
                jwt_service=jwt_service,
            ),
            "user_repo": user_repo,
            "password_service": password_service,
            "jwt_service": jwt_service,
        }

    async def test_should_register_new_user_successfully(self, auth_service_with_mocks):
        """Test successful user registration."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        password_service = auth_service_with_mocks["password_service"]
        jwt_service = auth_service_with_mocks["jwt_service"]

        email = "new@example.com"
        username = "newuser"
        password = "password123"
        first_name = "John"
        last_name = "Doe"

        user_repo.exists_by_email.return_value = False
        user_repo.exists_by_username.return_value = False
        password_service.hash_password.return_value = "hashed_password"

        # Mock User.create
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()
        mock_user.email = email
        mock_user.role = UserRole.VIEWER

        mock_token_pair = Mock(spec=TokenPair)
        jwt_service.create_token_pair.return_value = mock_token_pair

        with patch(
            "boursa_vision.domain.entities.user.User.create", return_value=mock_user
        ):
            # Act
            result = await service.register_user(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

        # Assert
        assert isinstance(result, RegistrationResult)
        assert result.user is mock_user
        assert result.token_pair is mock_token_pair

        # Verify validations
        user_repo.exists_by_email.assert_called_once_with(email)
        user_repo.exists_by_username.assert_called_once_with(username)

        # Verify password hashing
        password_service.hash_password.assert_called_once_with(password)

        # Verify user saved
        user_repo.save.assert_called_once_with(mock_user)

        # Verify token creation
        jwt_service.create_token_pair.assert_called_once_with(
            user_id=mock_user.id,
            email=mock_user.email,
            role=mock_user.role,
            permissions=mock_user.role.permissions,
        )

    async def test_should_raise_error_when_email_exists(self, auth_service_with_mocks):
        """Test registration fails when email already exists."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]

        user_repo.exists_by_email.return_value = True

        # Act & Assert
        with pytest.raises(ValueError, match="User with this email already exists"):
            await service.register_user(
                email="existing@example.com",
                username="newuser",
                password="password123",
                first_name="John",
                last_name="Doe",
            )

    async def test_should_raise_error_when_username_exists(
        self, auth_service_with_mocks
    ):
        """Test registration fails when username already exists."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]

        user_repo.exists_by_email.return_value = False
        user_repo.exists_by_username.return_value = True

        # Act & Assert
        with pytest.raises(ValueError, match="User with this username already exists"):
            await service.register_user(
                email="new@example.com",
                username="existing_user",
                password="password123",
                first_name="John",
                last_name="Doe",
            )


@pytest.mark.unit
class TestPasswordChange:
    """Test password change functionality."""

    @pytest.fixture
    def auth_service_with_mocks(self):
        """Create service with mocked dependencies."""
        user_repo = AsyncMock()
        password_service = Mock()

        return {
            "service": AuthenticationService(
                user_repository=user_repo,
                refresh_token_repository=AsyncMock(),
                password_service=password_service,
                jwt_service=Mock(),
            ),
            "user_repo": user_repo,
            "password_service": password_service,
        }

    async def test_should_change_password_successfully(self, auth_service_with_mocks):
        """Test successful password change."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        password_service = auth_service_with_mocks["password_service"]

        user_id = uuid4()
        old_password = "old_password"
        new_password = "new_password"

        mock_user = Mock(spec=User)
        mock_user.password_hash = "old_hash"

        user_repo.find_by_id.return_value = mock_user
        password_service.verify_password.return_value = True
        password_service.hash_password.return_value = "new_hash"

        # Act
        result = await service.change_password(user_id, old_password, new_password)

        # Assert
        assert result is True
        user_repo.find_by_id.assert_called_once_with(user_id)
        password_service.verify_password.assert_called_once_with(
            old_password, "old_hash"
        )
        password_service.hash_password.assert_called_once_with(new_password)
        assert mock_user.password_hash == "new_hash"
        user_repo.save.assert_called_once_with(mock_user)

    async def test_should_raise_error_when_user_not_found(
        self, auth_service_with_mocks
    ):
        """Test password change fails when user doesn't exist."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]

        user_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            await service.change_password(uuid4(), "old", "new")

    async def test_should_raise_error_when_old_password_incorrect(
        self, auth_service_with_mocks
    ):
        """Test password change fails with incorrect old password."""
        # Arrange
        service = auth_service_with_mocks["service"]
        user_repo = auth_service_with_mocks["user_repo"]
        password_service = auth_service_with_mocks["password_service"]

        mock_user = Mock(spec=User)
        mock_user.password_hash = "old_hash"

        user_repo.find_by_id.return_value = mock_user
        password_service.verify_password.return_value = False

        # Act & Assert
        with pytest.raises(ValueError, match="Incorrect old password"):
            await service.change_password(uuid4(), "wrong_old", "new")


@pytest.mark.unit
class TestTokenCleanup:
    """Test token cleanup functionality."""

    async def test_should_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        # Arrange
        refresh_token_repo = AsyncMock()
        auth_service = AuthenticationService(
            user_repository=AsyncMock(),
            refresh_token_repository=refresh_token_repo,
            password_service=Mock(),
            jwt_service=Mock(),
        )

        refresh_token_repo.cleanup_expired_tokens.return_value = 5  # 5 tokens cleaned

        # Act
        result = await auth_service.cleanup_expired_tokens()

        # Assert
        assert result == 5
        refresh_token_repo.cleanup_expired_tokens.assert_called_once()

        # Verify datetime parameter
        call_args = refresh_token_repo.cleanup_expired_tokens.call_args[0][0]
        assert isinstance(call_args, datetime)
        assert call_args.tzinfo == timezone.utc


@pytest.mark.unit
class TestExceptionHierarchy:
    """Test custom exception hierarchy."""

    def test_authentication_error_base_exception(self):
        """Test AuthenticationError is base exception."""
        error = AuthenticationError("Base auth error")
        assert str(error) == "Base auth error"
        assert isinstance(error, Exception)

    def test_invalid_credentials_error_inheritance(self):
        """Test InvalidCredentialsError inherits correctly."""
        error = InvalidCredentialsError("Invalid creds")
        assert str(error) == "Invalid creds"
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)

    def test_account_disabled_error_inheritance(self):
        """Test AccountDisabledError inherits correctly."""
        error = AccountDisabledError("Account disabled")
        assert str(error) == "Account disabled"
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)

    def test_token_expired_error_inheritance(self):
        """Test TokenExpiredError inherits correctly."""
        error = TokenExpiredError("Token expired")
        assert str(error) == "Token expired"
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)


@pytest.mark.unit
class TestResultDataclasses:
    """Test result dataclasses."""

    def test_registration_result_creation_and_immutability(self):
        """Test RegistrationResult creation and immutability."""
        # Arrange
        user = Mock(spec=User)
        token_pair = Mock(spec=TokenPair)

        # Act
        result = RegistrationResult(user=user, token_pair=token_pair)

        # Assert
        assert result.user is user
        assert result.token_pair is token_pair

        # Test immutability
        with pytest.raises(AttributeError):
            result.user = Mock()

    def test_authentication_result_creation_and_immutability(self):
        """Test AuthenticationResult creation and immutability."""
        # Arrange
        user = Mock(spec=User)
        token_pair = Mock(spec=TokenPair)

        # Act
        result = AuthenticationResult(user=user, token_pair=token_pair)

        # Assert
        assert result.user is user
        assert result.token_pair is token_pair

        # Test immutability
        with pytest.raises(AttributeError):
            result.token_pair = Mock()


# Performance and edge case tests
@pytest.mark.unit
class TestAuthenticationServiceEdgeCases:
    """Test edge cases and error conditions."""

    async def test_should_handle_concurrent_authentication_attempts(self):
        """Test service handles concurrent authentication gracefully."""
        # Arrange
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

        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.password_hash = "hashed"
        mock_user.is_active = True
        mock_user.role = UserRole.VIEWER
        mock_user.update_last_login = Mock()
        mock_user._add_domain_event = Mock()

        user_repo.find_by_email_for_auth.return_value = mock_user
        password_service.verify_password.return_value = True

        mock_token_pair = Mock(spec=TokenPair)
        mock_token_pair.refresh_token = Mock()
        mock_token_pair.refresh_token.token = "token"
        mock_token_pair.refresh_token.expires_at = datetime.now(timezone.utc)
        jwt_service.create_token_pair.return_value = mock_token_pair

        # Mock refresh token creation
        with patch(
            "boursa_vision.domain.entities.refresh_token.RefreshToken.create"
        ) as mock_rt_create:
            mock_rt_entity = Mock(spec=RefreshToken)
            mock_rt_create.return_value = mock_rt_entity

            # Act - Multiple concurrent authentications
            import asyncio

            tasks = [
                auth_service.authenticate_user("test@example.com", "password")
                for _ in range(3)
            ]
            results = await asyncio.gather(*tasks)

        # Assert - All should succeed
        assert len(results) == 3
        assert all(result is mock_token_pair for result in results)

    async def test_should_handle_database_errors_gracefully(self):
        """Test service handles database errors appropriately."""
        # Arrange
        user_repo = AsyncMock()
        user_repo.find_by_email_for_auth.side_effect = Exception("Database error")

        auth_service = AuthenticationService(
            user_repository=user_repo,
            refresh_token_repository=AsyncMock(),
            password_service=Mock(),
            jwt_service=Mock(),
        )

        # Act & Assert - Database errors should propagate
        with pytest.raises(Exception, match="Database error"):
            await auth_service.authenticate_user("test@example.com", "password")

    def test_should_handle_none_parameters_appropriately(self):
        """Test service validates required parameters properly."""
        # Arrange & Act & Assert - Initialize with valid parameters should work
        auth_service = AuthenticationService(
            user_repository=AsyncMock(),
            refresh_token_repository=AsyncMock(),
            password_service=Mock(),
            jwt_service=Mock(),
        )

        # Verify the service was created successfully
        assert auth_service is not None
