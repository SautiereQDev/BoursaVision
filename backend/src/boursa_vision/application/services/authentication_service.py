"""
Authentication Service - Application Layer
==========================================

Main authentication service that orchestrates user login, logout,
token generation, and validation operations.
"""

from dataclasses import dataclass
from datetime import UTC
from uuid import UUID

from ...domain.entities.refresh_token import RefreshToken as RefreshTokenEntity
from ...domain.entities.user import User
from ...domain.events.auth_events import (
    UserLoggedInEvent,
    UserLoggedOutEvent,
    UserLoginFailedEvent,
)
from ...domain.repositories.refresh_token_repository import IRefreshTokenRepository
from ...domain.repositories.user_repository import IUserRepository
from ...domain.value_objects.auth import TokenPair
from .jwt_service import JWTService
from .password_service import PasswordService


@dataclass(frozen=True)
class RegistrationResult:
    """Result from user registration containing user and tokens."""

    user: User
    token_pair: TokenPair


@dataclass(frozen=True)
class AuthenticationResult:
    """Result from user authentication containing user and tokens."""

    user: User
    token_pair: TokenPair


class AuthenticationError(Exception):
    """Base exception for authentication errors"""


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid"""


class AccountDisabledError(AuthenticationError):
    """Raised when account is disabled"""


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired"""


class AuthenticationService:
    """Main authentication service"""

    def __init__(
        self,
        user_repository: IUserRepository,
        refresh_token_repository: IRefreshTokenRepository,
        password_service: PasswordService,
        jwt_service: JWTService,
    ):
        """
        Initialize authentication service.

        Args:
            user_repository: User repository interface
            refresh_token_repository: Refresh token repository interface
            password_service: Password hashing service
            jwt_service: JWT token service
        """
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
        self.password_service = password_service
        self.jwt_service = jwt_service

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> TokenPair:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Token pair with access and refresh tokens

        Raises:
            InvalidCredentialsError: If credentials are invalid
            AccountDisabledError: If account is disabled
        """
        # Find user by email
        user = await self.user_repository.find_by_email_for_auth(email)

        if not user:
            # Failed login event will be handled elsewhere since we don't have user context
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        if not self.password_service.verify_password(password, user.password_hash):
            # Add failed login event
            user._add_domain_event(
                UserLoginFailedEvent(
                    email=email,
                    failure_reason="invalid_credentials",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
            raise InvalidCredentialsError("Invalid email or password")

        # Check if account is active
        if not user.is_active:
            # Add failed login event
            user._add_domain_event(
                UserLoginFailedEvent(
                    email=email,
                    failure_reason="account_disabled",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
            raise AccountDisabledError("Account is disabled")

        # Update last login
        user.update_last_login()
        await self.user_repository.update(user)

        # Create token pair
        token_pair = self.jwt_service.create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role,
            permissions=user.role.permissions,
        )

        # Save refresh token to repository
        refresh_token_entity = RefreshTokenEntity.create(
            token=token_pair.refresh_token.token,
            user_id=user.id,
            expires_at=token_pair.refresh_token.expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.refresh_token_repository.save(refresh_token_entity)

        # Add successful login event
        user._add_domain_event(
            UserLoggedInEvent(
                user_id=user.id,
                email=user.email,
                login_method="password",
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

        return token_pair

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New token pair

        Raises:
            TokenExpiredError: If refresh token is invalid or expired
        """
        # Find refresh token in repository
        token_entity = await self.refresh_token_repository.find_by_token(refresh_token)

        if not token_entity or not token_entity.is_valid():
            raise TokenExpiredError("Invalid or expired refresh token")

        # Get user
        user = await self.user_repository.find_by_id(token_entity.user_id)
        if not user or not user.is_active:
            raise TokenExpiredError("User not found or inactive")

        # Mark old token as used
        token_entity.use()

        # Create new token pair
        new_token_pair = self.jwt_service.create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role,
            permissions=user.role.permissions,
        )

        # Update refresh token in repository
        token_entity.token = new_token_pair.refresh_token.token
        token_entity.expires_at = new_token_pair.refresh_token.expires_at
        await self.refresh_token_repository.update(token_entity)

        return new_token_pair

    async def logout_user(
        self,
        user_id: UUID,
        refresh_token: str | None = None,
        logout_all_sessions: bool = False,
    ) -> None:
        """
        Logout user by revoking tokens.

        Args:
            user_id: User ID
            refresh_token: Specific refresh token to revoke
            logout_all_sessions: Whether to logout all user sessions
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            return

        if logout_all_sessions:
            # Revoke all refresh tokens for user
            await self.refresh_token_repository.revoke_all_for_user(
                user_id, reason="logout_all"
            )
            logout_method = "logout_all"
        elif refresh_token:
            # Revoke specific refresh token
            token_entity = await self.refresh_token_repository.find_by_token(
                refresh_token
            )
            if token_entity:
                token_entity.revoke("manual_logout")
                await self.refresh_token_repository.update(token_entity)
            logout_method = "manual"
        else:
            logout_method = "manual"

        # Add logout event
        user._add_domain_event(
            UserLoggedOutEvent(
                user_id=user.id,
                email=user.email,
                logout_method=logout_method,
            )
        )

    async def validate_access_token(self, token: str) -> User | None:
        """
        Validate access token and return user.

        Args:
            token: Access token string

        Returns:
            User if token is valid, None otherwise
        """
        payload = self.jwt_service.verify_access_token(token)
        if not payload:
            return None

        user_id_str = payload.get("sub")
        if not user_id_str:
            return None

        try:
            user_id = UUID(user_id_str)
            user = await self.user_repository.find_by_id(user_id)

            # Check if user is still active
            if user and user.is_active:
                return user
        except ValueError:
            pass

        return None

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> RegistrationResult:
        """
        Register a new user.

        Args:
            email: User email
            username: Username
            password: Plain text password
            first_name: First name
            last_name: Last name

        Returns:
            Registration result with user and tokens

        Raises:
            ValueError: If user already exists or validation fails
        """
        # Check if user already exists
        if await self.user_repository.exists_by_email(email):
            raise ValueError("User with this email already exists")

        if await self.user_repository.exists_by_username(username):
            raise ValueError("User with this username already exists")

        # Hash password
        password_hash = self.password_service.hash_password(password)

        # Create user
        user = User.create(
            email=email,
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )

        # Save user
        await self.user_repository.save(user)

        # Generate token pair for the new user
        token_pair = self.jwt_service.create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role,
            permissions=user.role.permissions,
        )

        return RegistrationResult(user=user, token_pair=token_pair)

    async def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            ValueError: If user doesn't exist or old password is incorrect
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify old password
        if not self.password_service.verify_password(old_password, user.password_hash):
            raise ValueError("Incorrect old password")

        # Hash new password
        new_password_hash = self.password_service.hash_password(new_password)

        # Update user
        user.password_hash = new_password_hash
        await self.user_repository.save(user)

        return True

    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired refresh tokens.

        Returns:
            Number of tokens cleaned up
        """
        from datetime import datetime

        return await self.refresh_token_repository.cleanup_expired_tokens(
            datetime.now(UTC)
        )
