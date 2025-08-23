"""
FastAPI dependencies for dependency injection
"""

from typing import Any, Optional, Protocol

from fastapi import Query

from boursa_vision.application.services.authentication_service import (
    AuthenticationService,
)
from boursa_vision.application.services.jwt_service import JWTService
from boursa_vision.application.services.password_service import PasswordService
from boursa_vision.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from boursa_vision.domain.repositories.user_repository import UserRepository


class ContainerProtocol(Protocol):
    """Protocol for dependency injection container."""

    def auth_service(self) -> AuthenticationService:
        """Get authentication service."""
        ...

    def jwt_service(self) -> JWTService:
        """Get JWT service."""
        ...

    def password_service(self) -> PasswordService:
        """Get password service."""
        ...

    def user_repository(self) -> UserRepository:
        """Get user repository."""
        ...

    def refresh_token_repository(self) -> RefreshTokenRepository:
        """Get refresh token repository."""
        ...


# Temporary container for dependency injection
class Container:
    """Temporary dependency container."""

    def __init__(self):
        self._services = {}
        self._auth_service: AuthenticationService | None = None
        self._jwt_service: JWTService | None = None
        self._password_service: PasswordService | None = None
        self._user_repository: UserRepository | None = None
        self._refresh_token_repository: RefreshTokenRepository | None = None

    def get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        return self._services.get(service_name)

    def auth_service(self) -> AuthenticationService:
        """Get authentication service."""
        if self._auth_service is None:
            # This will be properly initialized when container is set up
            raise RuntimeError("AuthenticationService not initialized")
        return self._auth_service

    def jwt_service(self) -> JWTService:
        """Get JWT service."""
        if self._jwt_service is None:
            raise RuntimeError("JWTService not initialized")
        return self._jwt_service

    def password_service(self) -> PasswordService:
        """Get password service."""
        if self._password_service is None:
            raise RuntimeError("PasswordService not initialized")
        return self._password_service

    def user_repository(self) -> UserRepository:
        """Get user repository."""
        if self._user_repository is None:
            raise RuntimeError("UserRepository not initialized")
        return self._user_repository

    def refresh_token_repository(self) -> RefreshTokenRepository:
        """Get refresh token repository."""
        if self._refresh_token_repository is None:
            raise RuntimeError("RefreshTokenRepository not initialized")
        return self._refresh_token_repository

    def set_auth_service(self, service: AuthenticationService) -> None:
        """Set authentication service."""
        self._auth_service = service

    def set_jwt_service(self, service: JWTService) -> None:
        """Set JWT service."""
        self._jwt_service = service

    def set_password_service(self, service: PasswordService) -> None:
        """Set password service."""
        self._password_service = service

    def set_user_repository(self, repository: UserRepository) -> None:
        """Set user repository."""
        self._user_repository = repository

    def set_refresh_token_repository(self, repository: RefreshTokenRepository) -> None:
        """Set refresh token repository."""
        self._refresh_token_repository = repository


# Global container instance
_container = Container()


def get_container() -> Container:
    """Get the dependency injection container."""
    return _container


# User authentication dependency (simplified for now)
CurrentUserOptional = Optional[Any]


def get_current_user_optional() -> CurrentUserOptional:
    """Get current user (optional, returns None for now)."""
    # TODO: Implement actual authentication
    return None


# Pagination dependency
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> dict[str, int]:
    """Get pagination parameters."""
    offset = (page - 1) * page_size
    return {"page": page, "page_size": page_size, "offset": offset, "limit": page_size}


# Type aliases for cleaner imports
PaginationParams = dict[str, int]


def get_database_session():
    """Get database session dependency."""
    # TODO: Implement actual database session
    return None
