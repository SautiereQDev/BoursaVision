"""
Authentication Dependencies for FastAPI
======================================

FastAPI dependencies for authentication and authorization.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from boursa_vision.application.services.authentication_service import (
    AuthenticationService,
)
from boursa_vision.domain.entities.user import User

# TODO: Fix circular import issue with get_container
# from ..dependencies import get_container


# Security scheme
security = HTTPBearer()


async def get_auth_service() -> AuthenticationService:
    """Get authentication service from container"""
    # TODO: Fix circular import and implement proper container
    raise NotImplementedError("Container dependency needs to be fixed")
    # container = get_container()
    # return container.auth_service()


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> User | None:
    """
    Get current user from JWT token (optional).

    Returns None if no token or invalid token.
    """
    if not credentials:
        return None

    try:
        user = await auth_service.validate_access_token(credentials.credentials)
        return user
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> User:
    """
    Get current user from JWT token (required).

    Raises HTTPException if no token or invalid token.
    """
    try:
        user = await auth_service.validate_access_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.

    Raises HTTPException if user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.

    Args:
        required_role: Required user role

    Returns:
        Dependency function
    """

    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role.value != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return current_user

    return role_dependency


def require_permission(required_permission: str):
    """
    Create a dependency that requires a specific permission.

    Args:
        required_permission: Required permission

    Returns:
        Dependency function
    """

    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not current_user.has_permission(required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required",
            )
        return current_user

    return permission_dependency


# Common role dependencies
require_admin = require_role("admin")
require_premium = require_role("premium")
require_basic = require_role("basic")

# Common permission dependencies
require_create_portfolio = require_permission("create_portfolio")
require_execute_trades = require_permission("execute_trades")
require_view_analytics = require_permission("view_analytics")
require_manage_system = require_permission("manage_system")
require_view_advanced_analytics = require_permission("view_advanced_analytics")
require_access_admin_panel = require_permission("access_admin_panel")


# Type aliases for easier imports
CurrentUser = User
CurrentUserOptional = User | None
