"""
Example Protected Routes
========================

Examples of how to use authentication in FastAPI routes.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from boursa_vision.domain.entities.user import User
from boursa_vision.infrastructure.web.dependencies.auth_dependencies import (
    get_current_active_user,
    require_admin,
    require_create_portfolio,
    require_execute_trades,
    require_premium,
    require_view_analytics,
)

# Example router
router = APIRouter(prefix="/api/v1/protected", tags=["Protected Routes"])


@router.get(
    "/profile",
    summary="Get user profile",
    description="Get current user's profile (requires authentication)",
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get current user's profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "permissions": current_user.role.permissions,
    }


@router.get(
    "/admin-only",
    summary="Admin only endpoint",
    description="Endpoint accessible only by admin users",
)
async def admin_only_endpoint(
    current_user: User = Depends(require_admin),
) -> Dict[str, str]:
    """Admin only endpoint."""
    return {
        "message": f"Hello admin {current_user.email}!",
        "role": current_user.role.value,
    }


@router.get(
    "/premium-only",
    summary="Premium only endpoint",
    description="Endpoint accessible only by premium users",
)
async def premium_only_endpoint(
    current_user: User = Depends(require_premium),
) -> Dict[str, str]:
    """Premium only endpoint."""
    return {
        "message": f"Hello premium user {current_user.email}!",
        "role": current_user.role.value,
    }


@router.post(
    "/portfolios",
    summary="Create portfolio",
    description="Create a new portfolio (requires create_portfolio permission)",
)
async def create_portfolio(
    current_user: User = Depends(require_create_portfolio),
) -> Dict[str, Any]:
    """Create a new portfolio."""
    return {
        "message": "Portfolio creation endpoint",
        "user_id": current_user.id,
        "permissions": current_user.role.permissions,
    }


@router.post(
    "/trades",
    summary="Execute trade",
    description="Execute a trade (requires execute_trades permission)",
)
async def execute_trade(
    current_user: User = Depends(require_execute_trades),
) -> Dict[str, Any]:
    """Execute a trade."""
    return {
        "message": "Trade execution endpoint",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }


@router.get(
    "/analytics",
    summary="View analytics",
    description="View analytics data (requires view_analytics permission)",
)
async def view_analytics(
    current_user: User = Depends(require_view_analytics),
) -> Dict[str, Any]:
    """View analytics data."""
    return {
        "message": "Analytics data endpoint",
        "user_id": current_user.id,
        "analytics": {
            "portfolio_performance": "sample_data",
            "risk_metrics": "sample_data",
        },
    }


@router.get(
    "/users",
    summary="List all users",
    description="List all users (admin only)",
)
async def list_users(
    current_user: User = Depends(require_admin),
) -> Dict[str, List[str]]:
    """List all users (admin only)."""
    return {
        "message": "User management endpoint",
        "users": ["sample_user_1", "sample_user_2"],
    }


@router.get(
    "/role-info",
    summary="Get role information",
    description="Get information about user's role and permissions",
)
async def get_role_info(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get role and permission information."""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value,
        "permissions": current_user.role.permissions,
        "role_description": {
            "admin": "Full system access and user management",
            "premium": "Portfolio creation, trade execution, and advanced analytics",
            "basic": "Basic portfolio viewing and simple analytics",
        }.get(current_user.role.value, "Unknown role"),
    }
