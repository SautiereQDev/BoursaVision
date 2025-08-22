"""
Authentication Module Initialization
====================================

This module initializes all authentication-related components.
"""

from boursa_vision.infrastructure.web.dependencies.auth_dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
    require_role,
    require_permission,
    require_admin,
    require_premium,
    require_basic,
    require_create_portfolio,
    require_execute_trades,
    require_view_analytics,
    require_manage_system,
    require_view_advanced_analytics,
    require_access_admin_panel,
)

from boursa_vision.infrastructure.web.routes.auth_routes import router as auth_router

# TODO: Fix circular import issue with Container and CurrentUserOptional
# from boursa_vision.infrastructure.web.dependencies import Container, CurrentUserOptional

__all__ = [
    # Dependencies
    "get_current_user",
    "get_current_user_optional", 
    "get_current_active_user",
    "require_role",
    "require_permission",
    "require_admin",
    "require_premium",
    "require_basic",
    "require_create_portfolio",
    "require_execute_trades",
    "require_view_analytics",
    "require_manage_system",
    "require_view_advanced_analytics",
    "require_access_admin_panel",
    # TODO: Add when circular import is fixed
    # "Container",
    # "CurrentUserOptional",
    # Router
    "auth_router",
]
