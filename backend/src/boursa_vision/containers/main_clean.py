"""
Main Container - Application Composition Root (Clean)
===================================================

MainContainer is the composition root that wires together all containers
following dependency injection principles. This is the single entry point
for the entire application's dependency graph.

Features:
- Container composition and wiring
- Dependency graph management
- Configuration orchestration
- Application lifecycle management
- Clean shutdown handling

Architecture: Clean Architecture with CQRS + Dependency Injection
"""

from dependency_injector import containers, providers

from .core import CoreContainer
from .database import DatabaseContainer  
from .repositories import RepositoryContainer
from .services import ServicesContainer
from .application import ApplicationContainer
from .infrastructure import InfrastructureContainer
from .web_simple import WebContainer


class MainContainer(containers.DeclarativeContainer):
    """
    Main composition root for the entire application.
    
    This container wires together all other containers following 
    Clean Architecture principles with proper dependency direction:
    
    Core (innermost) -> Database -> Repository -> Services -> 
    Application -> Infrastructure -> Web (outermost)
    
    Each container depends only on containers in inner layers,
    maintaining clean architecture dependency rules.
    """
    
    # =============================================================================
    # CONTAINER HIERARCHY (CLEAN ARCHITECTURE LAYERS)
    # =============================================================================
    
    # Layer 1: Core (Domain + Configuration)
    core = providers.Container(
        CoreContainer,
    )
    
    # Layer 2: Database (Persistence Infrastructure)
    database = providers.Container(
        DatabaseContainer,
        core=core,
    )
    
    # Layer 3: Repository (Data Access Layer)
    repositories = providers.Container(
        RepositoryContainer,
        database=database,
        core=core,
    )
    
    # Layer 4: Domain Services (Business Logic)
    services = providers.Container(
        ServicesContainer,
        repositories=repositories,
        core=core,
    )
    
    # Layer 5: Application (Use Cases / CQRS)
    application = providers.Container(
        ApplicationContainer,
        repositories=repositories,
        services=services,
    )
    
    # Layer 6: Infrastructure (External Services)
    infrastructure = providers.Container(
        InfrastructureContainer,
        core=core,
    )
    
    # Layer 7: Web (HTTP Layer)
    web = providers.Container(
        WebContainer,
        application=application,
        infrastructure=infrastructure,
        core=core,
    )
    
    # =============================================================================
    # APPLICATION ENTRY POINTS
    # =============================================================================
    
    # FastAPI application instance for web serving
    app = providers.Factory(
        _create_application,
        fastapi_app=web.fastapi_app,
        portfolio_router=web.portfolio_router,
        investment_router=web.investment_router,
        auth_router=web.auth_router,
        health_router=web.health_router,
    )
    
    # Background task worker for Celery
    worker = providers.Factory(
        _create_worker,
        celery_app=infrastructure.celery_app,
    )


# =============================================================================
# APPLICATION FACTORY FUNCTIONS
# =============================================================================

def _create_application(
    fastapi_app,
    portfolio_router,
    investment_router,
    auth_router,
    health_router
):
    """Create complete FastAPI application with all routers."""
    
    # Include all routers
    fastapi_app.include_router(portfolio_router)
    fastapi_app.include_router(investment_router)
    fastapi_app.include_router(auth_router)
    fastapi_app.include_router(health_router)
    
    # Add middleware (CORS, logging, etc.)
    from fastapi.middleware.cors import CORSMiddleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @fastapi_app.get("/")
    def root():
        return {
            "message": "BoursaVision API",
            "version": "1.0.0",
            "architecture": "Clean Architecture + CQRS + DI",
            "containers": [
                "CoreContainer",
                "DatabaseContainer", 
                "RepositoryContainer",
                "ServicesContainer",
                "ApplicationContainer",
                "InfrastructureContainer",
                "WebContainer"
            ]
        }
    
    return fastapi_app


def _create_worker(celery_app):
    """Create Celery worker for background tasks."""
    return celery_app


# =============================================================================
# CONTAINER UTILITY FUNCTIONS  
# =============================================================================

def create_container() -> MainContainer:
    """
    Factory function to create and configure the main container.
    
    This is the primary entry point for dependency injection setup.
    Use this function in your application startup to get a fully
    configured container with all dependencies properly wired.
    """
    container = MainContainer()
    return container


def create_app_from_container(container: MainContainer):
    """
    Create FastAPI application from configured container.
    
    Args:
        container: Fully configured MainContainer
        
    Returns:
        FastAPI application ready to serve
    """
    return container.app()


def create_worker_from_container(container: MainContainer):
    """
    Create Celery worker from configured container.
    
    Args:
        container: Fully configured MainContainer
        
    Returns:
        Celery application ready for task processing
    """
    return container.worker()
