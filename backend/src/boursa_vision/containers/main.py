"""
Main Container - Application Composition Root
===========================================

MainContainer is the composition root that wires together all containerfrom dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .core import CoreContainer
from .database import DatabaseContainer
from .repositories import RepositoryContainer
from .services import ServicesContainer
from .application import ApplicationContainer
from .infrastructure import InfrastructureContainer
from .web_simple import WebContainer


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


class MainContainer(containers.DeclarativeContainer):ependency injection principles. This is the single entry point
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

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .core import CoreContainer
from .database import DatabaseContainer
from .repositories import RepositoryContainer
from .services import ServicesContainer
from .application import ApplicationContainer
from .infrastructure import InfrastructureContainer
from .web import WebContainer


class MainContainer(containers.DeclarativeContainer):
    """
    Main application container orchestrating all dependency injection.
    
    This container serves as the composition root for the entire application,
    ensuring proper dependency graph resolution and lifecycle management
    across all architectural layers.
    
    Container Architecture:
        CoreContainer -> DatabaseContainer -> RepositoryContainer
                      -> InfrastructureContainer -> ServicesContainer
                                                 -> ApplicationContainer
                                                 -> WebContainer
    
    Features:
        - Environment-aware configuration
        - Proper container lifecycle management
        - FastAPI integration via wiring
        - Centralized dependency resolution
        - Resource management and cleanup
    """
    
    # =============================================================================
    # CORE FOUNDATION CONTAINERS
    # =============================================================================
    
    # Core services (configuration, logging, metrics)
    core = providers.Container(
        CoreContainer,
    )
    
    # Database connections and session management
    database = providers.Container(
        DatabaseContainer,
        config=core.config,
        logger=core.logger,
    )
    
    # =============================================================================
    # BUSINESS LOGIC CONTAINERS
    # =============================================================================
    
    # Repository layer for data access
    repositories = providers.Container(
        RepositoryContainer,
        session_factory=database.session_factory,
        timescale_session_factory=database.timescale_session_factory,
        redis_client=database.redis_client,
        cache_client=database.cache_client,
    )
    
    # Domain services for business logic
    services = providers.Container(
        ServicesContainer,
        repositories=repositories,
    )
    
    # Application layer for CQRS commands and queries
    application = providers.Container(
        ApplicationContainer,
        repositories=repositories,
        services=services,
    )
    
    # =============================================================================
    # INFRASTRUCTURE AND EXTERNAL SERVICES
    # =============================================================================
    
    # Infrastructure services and external integrations
    infrastructure = providers.Container(
        InfrastructureContainer,
        config=core.config,
        logger=core.logger,
    )
    
    # =============================================================================
    # WEB LAYER AND API
    # =============================================================================
    
    # Web layer with FastAPI integration
    web = providers.Container(
        WebContainer,
        application=application,
        infrastructure=infrastructure,
    )
    
    # =============================================================================
    # APPLICATION ENTRY POINTS
    # =============================================================================
    
    # Main FastAPI application instance
    app = providers.Factory(
        _create_wired_fastapi_app,
        fastapi_app=web.fastapi_app,
        container=providers.Self(),
    )
    
    # Background task processor (Celery)
    celery_app = providers.Factory(
        _create_wired_celery_app,
        celery_app=infrastructure.celery_app,
        container=providers.Self(),
    )
    
    # =============================================================================
    # DEVELOPMENT AND TESTING UTILITIES
    # =============================================================================
    
    # Database initializer for development/testing
    db_initializer = providers.Factory(
        _create_database_initializer,
        engine=database.engine,
        timescale_engine=database.timescale_engine,
        logger=core.logger,
    )
    
    # Test data seeder for development
    test_data_seeder = providers.Factory(
        _create_test_data_seeder,
        session_factory=database.session_factory,
        logger=core.logger,
    )


# =============================================================================
# WIRING CONFIGURATION FOR FASTAPI
# =============================================================================

# Define modules to wire for automatic dependency injection
FASTAPI_WIRING_MODULES = [
    "boursa_vision.web.routers.auth_router",
    "boursa_vision.web.routers.portfolio_router", 
    "boursa_vision.web.routers.investment_router",
    "boursa_vision.web.routers.transaction_router",
    "boursa_vision.web.routers.market_data_router",
    "boursa_vision.web.routers.analytics_router",
    "boursa_vision.web.routers.health_router",
    "boursa_vision.web.routers.metrics_router",
    "boursa_vision.web.websockets.market_websocket_handler",
    "boursa_vision.web.websockets.portfolio_websocket_handler",
    "boursa_vision.web.middleware.auth_middleware",
    "boursa_vision.web.error_handling.error_handler",
]

# Define modules to wire for Celery background tasks
CELERY_WIRING_MODULES = [
    "boursa_vision.infrastructure.tasks.market_data_tasks",
    "boursa_vision.infrastructure.tasks.portfolio_tasks",
    "boursa_vision.infrastructure.tasks.notification_tasks",
    "boursa_vision.infrastructure.tasks.analytics_tasks",
    "boursa_vision.infrastructure.tasks.maintenance_tasks",
]


# =============================================================================
# APPLICATION FACTORY FUNCTIONS
# =============================================================================

def _create_wired_fastapi_app(fastapi_app, container):
    """
    Create FastAPI application with proper dependency injection wiring.
    
    This function sets up the FastAPI app with all necessary middleware,
    routers, and dependency injection wiring for clean architecture.
    """
    from boursa_vision.web.app_configurator import configure_fastapi_app
    
    # Configure FastAPI app with middleware and routers
    configured_app = configure_fastapi_app(
        app=fastapi_app,
        cors_middleware=container.web.cors_middleware(),
        auth_middleware=container.web.auth_middleware(),
        security_middleware=container.web.security_headers_middleware(),
        error_handler=container.web.error_handler(),
        routers=[
            container.web.auth_router(),
            container.web.portfolio_router(),
            container.web.investment_router(),
            container.web.transaction_router(),
            container.web.market_data_router(),
            container.web.analytics_router(),
            container.web.health_router(),
            container.web.metrics_router(),
        ],
        websocket_handlers=[
            container.web.market_websocket_handler(),
            container.web.portfolio_websocket_handler(),
        ],
    )
    
    # Wire dependency injection for automatic resolution
    container.wire(modules=FASTAPI_WIRING_MODULES)
    
    return configured_app


def _create_wired_celery_app(celery_app, container):
    """
    Create Celery application with proper dependency injection wiring.
    
    This function sets up background task processing with access to
    all necessary services through dependency injection.
    """
    from boursa_vision.infrastructure.tasks.celery_configurator import configure_celery_app
    
    # Configure Celery app with tasks and settings
    configured_celery = configure_celery_app(
        celery_app=celery_app,
        container=container,
    )
    
    # Wire dependency injection for background tasks
    container.wire(modules=CELERY_WIRING_MODULES)
    
    return configured_celery


def _create_database_initializer(engine, timescale_engine, logger):
    """Create database initializer for schema setup and migrations."""
    from boursa_vision.infrastructure.database.initializer import DatabaseInitializer
    return DatabaseInitializer(
        engine=engine,
        timescale_engine=timescale_engine,
        logger=logger,
    )


def _create_test_data_seeder(session_factory, logger):
    """Create test data seeder for development environment."""
    from boursa_vision.infrastructure.database.test_data_seeder import TestDataSeeder
    return TestDataSeeder(
        session_factory=session_factory,
        logger=logger,
    )


# =============================================================================
# CONTAINER LIFECYCLE MANAGEMENT
# =============================================================================

class ContainerManager:
    """
    Container lifecycle manager for proper startup/shutdown handling.
    
    This class provides utilities for container initialization,
    resource allocation, and cleanup during application lifecycle.
    """
    
    def __init__(self, container: MainContainer):
        self.container = container
        self._initialized = False
    
    async def initialize(self):
        """Initialize all container resources and dependencies."""
        if self._initialized:
            return
        
        # Initialize database connections
        await self.container.database.initialize()
        
        # Initialize Redis connections
        await self.container.database.initialize_redis()
        
        # Initialize external service connections
        await self.container.infrastructure.initialize()
        
        # Run database migrations if needed
        await self.container.db_initializer().initialize_schema()
        
        # Seed test data in development environment
        if self.container.core.config().environment == "development":
            await self.container.test_data_seeder().seed_test_data()
        
        self._initialized = True
    
    async def cleanup(self):
        """Clean up all container resources and connections."""
        if not self._initialized:
            return
        
        # Cleanup database connections
        await self.container.database.cleanup()
        
        # Cleanup Redis connections
        await self.container.database.cleanup_redis()
        
        # Cleanup external service connections
        await self.container.infrastructure.cleanup()
        
        # Unwire dependency injection
        self.container.unwire()
        
        self._initialized = False


# =============================================================================
# DEPENDENCY INJECTION UTILITIES
# =============================================================================

def get_container() -> MainContainer:
    """
    Get the main application container instance.
    
    This function provides access to the container for manual
    dependency resolution when needed (e.g., in tests or scripts).
    """
    return MainContainer()


@inject
def get_repository_container(
    repositories: RepositoryContainer = Provide[MainContainer.repositories]
) -> RepositoryContainer:
    """Get repository container for direct data access needs."""
    return repositories


@inject
def get_application_container(
    application: ApplicationContainer = Provide[MainContainer.application]
) -> ApplicationContainer:
    """Get application container for CQRS command/query handling."""
    return application


@inject
def get_infrastructure_container(
    infrastructure: InfrastructureContainer = Provide[MainContainer.infrastructure]
) -> InfrastructureContainer:
    """Get infrastructure container for external service access."""
    return infrastructure
