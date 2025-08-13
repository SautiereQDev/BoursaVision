"""
FastAPI dependencies for dependency injection
"""
from typing import Dict, Optional, Any
from fastapi import Depends, Query


# Temporary container for dependency injection
class Container:
    """Temporary dependency container."""
    
    def __init__(self):
        self._services = {}
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        return self._services.get(service_name)


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
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
) -> Dict[str, int]:
    """Get pagination parameters."""
    offset = (page - 1) * page_size
    return {
        "page": page,
        "page_size": page_size,
        "offset": offset,
        "limit": page_size
    }


# Type aliases for cleaner imports
PaginationParams = Dict[str, int]


def get_database_session():
    """Get database session dependency."""
    # TODO: Implement actual database session
    return None
