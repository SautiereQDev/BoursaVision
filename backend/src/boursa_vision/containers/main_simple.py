"""
Main Container - Application Composition Root (Simplified)
========================================================

MainContainer is the composition root that wires together all containers
following Clean Architecture dependency rules.
"""

from dependency_injector import containers, providers

from .core import CoreContainer
from .database import DatabaseContainer
from .repositories_simple import RepositoryContainer
from .services import ServicesContainer
from .application import ApplicationContainer
from .infrastructure import InfrastructureContainer
from .web_simple import WebContainer


# =============================================================================
# APPLICATION FACTORY FUNCTIONS
# =============================================================================

def _create_application(fastapi_app):
    """Create complete FastAPI application (simplified)."""
    
    # Root endpoint
    @fastapi_app.get("/")
    def root():
        return {
            "message": "BoursaVision API", 
            "version": "1.0.0",
            "status": "running"
        }
    
    return fastapi_app


def _create_worker():
    """Create Celery worker (mock)."""
    class MockWorker:
        def __init__(self):
            self.status = "running"
    
    return MockWorker()


class MainContainer(containers.DeclarativeContainer):
    """
    Main composition root for the entire application.
    
    This container wires together all other containers following 
    Clean Architecture principles with proper dependency direction.
    """
    
    # Layer 1: Core (Domain + Configuration)
    core = providers.Container(
        CoreContainer,
    )
    
    # Layer 2: Database (Persistence Infrastructure)
    database = providers.Container(
        DatabaseContainer,
        config=core.config,
    )
    
    # Layer 3: Repository (Data Access Layer)
    repositories = providers.Container(
        RepositoryContainer,
        database=database,
    )
    
    # Layer 4: Domain Services (Business Logic)
    services = providers.Container(
        ServicesContainer,
        repositories=repositories,
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
    
    # Application entry points
    app = providers.Factory(
        _create_application,
        fastapi_app=web.fastapi_app,
    )
    
    worker = providers.Factory(
        _create_worker,
    )


class ContainerManager:
    """Helper class for container lifecycle management."""
    
    def __init__(self):
        self.container = MainContainer()
    
    def initialize(self):
        """Initialize the container and all dependencies."""
        # In a real implementation, this would:
        # - Load configuration
        # - Initialize database connections
        # - Set up logging
        # - Wire dependencies
        print("Container initialized successfully")
        return self.container
    
    def shutdown(self):
        """Clean shutdown of all resources."""
        # In a real implementation, this would:
        # - Close database connections
        # - Clean up background tasks
        # - Flush logs
        print("Container shut down successfully")
