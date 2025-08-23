"""
Authentication Middleware
========================

Middleware for JWT token validation and user authentication.
"""

import typing
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from boursa_vision.application.services.authentication_service import (
    AuthenticationService,
)
from boursa_vision.domain.entities.user import User


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication"""

    # Paths that don't require authentication
    EXCLUDED_PATHS: typing.ClassVar[set[str]] = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }

    def __init__(self, app, auth_service: AuthenticationService):
        """
        Initialize authentication middleware.

        Args:
            app: FastAPI application
            auth_service: Authentication service
        """
        super().__init__(app)
        self.auth_service = auth_service
        self.security = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication"""

        # Skip authentication for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Try to get authorization header
        authorization = request.headers.get("Authorization")

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token from Bearer header
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization[7:]  # Remove "Bearer " prefix

        # Validate token and get user
        user = await self.auth_service.validate_access_token(token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add user to request state
        request.state.current_user = user

        return await call_next(request)


class RequireRole:
    """Dependency to require specific role"""

    def __init__(self, required_role: str):
        """
        Initialize role requirement.

        Args:
            required_role: Required user role
        """
        self.required_role = required_role

    def __call__(self, request: Request) -> User:
        """
        Check if user has required role.

        Args:
            request: FastAPI request

        Returns:
            Current user if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        user: User | None = getattr(request.state, "current_user", None)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if user.role.value != self.required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{self.required_role}' required",
            )

        return user


class RequirePermission:
    """Dependency to require specific permission"""

    def __init__(self, required_permission: str):
        """
        Initialize permission requirement.

        Args:
            required_permission: Required permission
        """
        self.required_permission = required_permission

    def __call__(self, request: Request) -> User:
        """
        Check if user has required permission.

        Args:
            request: FastAPI request

        Returns:
            Current user if authorized

        Raises:
            HTTPException: If user doesn't have required permission
        """
        user: User | None = getattr(request.state, "current_user", None)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if not user.has_permission(self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{self.required_permission}' required",
            )

        return user


# Convenience instances
require_admin = RequireRole("admin")
require_premium = RequireRole("premium")
require_basic = RequireRole("basic")

require_create_portfolio = RequirePermission("create_portfolio")
require_execute_trades = RequirePermission("execute_trades")
require_view_analytics = RequirePermission("view_analytics")
require_manage_system = RequirePermission("manage_system")
