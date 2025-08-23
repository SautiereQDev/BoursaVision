"""
Authentication Module Initialization
====================================

This module initializes all authentication-related components.
"""

from boursa_vision.infrastructure.web.dependencies.auth_dependencies import (
    get_current_active_user,
    get_current_user,
    get_current_user_optional,
    require_access_admin_panel,
    require_admin,
    require_basic,
    require_create_portfolio,
    require_execute_trades,
    require_manage_system,
    require_permission,
    require_premium,
    require_role,
    require_view_advanced_analytics,
    require_view_analytics,
)
from boursa_vision.infrastructure.web.routes.auth_routes import router as auth_router

# TODO: Fix circular import issue with Container and CurrentUserOptional
# from boursa_vision.infrastructure.web.dependencies import Container, CurrentUserOptional

__all__ = [
    # TODO: Add when circular import is fixed
    # "Container",
    # "CurrentUserOptional",
    # Router
    "auth_router",
    "get_current_active_user",
    # Dependencies
    "get_current_user",
    "get_current_user_optional",
    "require_access_admin_panel",
    "require_admin",
    "require_basic",
    "require_create_portfolio",
    "require_execute_trades",
    "require_manage_system",
    "require_permission",
    "require_premium",
    "require_role",
    "require_view_advanced_analytics",
    "require_view_analytics",
]
