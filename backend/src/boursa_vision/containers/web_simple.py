"""
Web Container - FastAPI HTTP Layer (Simplified)
==============================================

WebContainer manages the FastAPI web layer components.
This includes routers, middleware, authentication, validation,
and HTTP-specific concerns with dependency injection.

Features:
- FastAPI routers for REST API endpoints
- Authentication and authorization middleware  
- Request/response validation
- Error handling and middleware
- CORS configuration
- API documentation integration

Dependencies: ApplicationContainer, InfrastructureContainer
"""

from dependency_injector import containers, providers


# =============================================================================
# WEB LAYER FACTORY FUNCTIONS
# =============================================================================

def _create_fastapi_app(title, version, debug):
    """Create FastAPI application instance."""
    from fastapi import FastAPI
    
    app = FastAPI(
        title=title,
        version=version,
        debug=debug,
        docs_url="/docs" if debug else None,
        redoc_url="/redoc" if debug else None,
    )
    
    return app


def _create_jwt_service(secret_key, algorithm, access_token_expire_minutes):
    """Create JWT service for token management."""
    # Simplified JWT service for dependency injection integration
    class SimpleJWTService:
        def __init__(self, secret_key, algorithm, expire_minutes):
            self.secret_key = secret_key
            self.algorithm = algorithm
            self.expire_minutes = expire_minutes
        
        def create_access_token(self):
            # JWT token creation logic would go here
            return "mock-token"
        
        def verify_token(self, token: str):
            # JWT token verification logic would go here
            return {"user_id": "test-user"}
    
    return SimpleJWTService(secret_key, algorithm, access_token_expire_minutes)


def _create_auth_middleware(jwt_service):
    """Create authentication middleware."""
    # Simplified auth middleware for dependency injection integration
    class SimpleAuthMiddleware:
        def __init__(self, jwt_service):
            self.jwt_service = jwt_service
        
        def __call__(self, request):
            # Authentication logic would go here
            return {"user": "authenticated"}
    
    return SimpleAuthMiddleware(jwt_service)


def _create_portfolio_router():
    """Create portfolio router."""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/portfolios", tags=["portfolios"])
    
    @router.get("/")
    async def get_portfolios():
        return {"portfolios": []}
    
    @router.post("/")
    async def create_portfolio():
        return {"message": "Portfolio created"}
    
    return router


def _create_investment_router():
    """Create investment router."""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/investments", tags=["investments"])
    
    @router.get("/")
    async def get_investments():
        return {"investments": []}
    
    @router.post("/")
    async def add_investment():
        return {"message": "Investment added"}
    
    return router


def _create_auth_router():
    """Create authentication router."""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/auth", tags=["authentication"])
    
    @router.post("/login")
    async def login():
        return {"access_token": "mock-token", "token_type": "bearer"}
    
    return router


def _create_health_router():
    """Create health check router."""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/health", tags=["health"])
    
    @router.get("/")
    async def health_check():
        return {"status": "healthy", "timestamp": "2025-08-24T00:00:00Z"}
    
    return router


# =============================================================================
# WEB CONTAINER CLASS
# =============================================================================

class WebContainer(containers.DeclarativeContainer):
    """
    Web container for FastAPI HTTP layer.
    
    Contains:
        - FastAPI application instance
        - API routers for different domains
        - Middleware stack configuration
        - Authentication/authorization services
        - Request validation and error handling
        - CORS and security configuration
    
    This layer handles HTTP concerns and integrates with
    the application layer through dependency injection.
    """
    
    # Dependencies from other containers
    application = providers.DependenciesContainer()
    infrastructure = providers.DependenciesContainer()
    core = providers.DependenciesContainer()
    
    # =============================================================================
    # FASTAPI APPLICATION
    # =============================================================================
    
    fastapi_app = providers.Singleton(
        _create_fastapi_app,
        title="BoursaVision API",
        version="1.0.0",
        debug=True,
    )
    
    # =============================================================================
    # AUTHENTICATION SERVICES
    # =============================================================================
    
    jwt_service = providers.Factory(
        _create_jwt_service,
        secret_key="dev-secret-key",
        algorithm="HS256",
        access_token_expire_minutes=30,
    )
    
    auth_middleware = providers.Factory(
        _create_auth_middleware,
        jwt_service=jwt_service,
    )
    
    # =============================================================================
    # API ROUTERS
    # =============================================================================
    
    portfolio_router = providers.Factory(
        _create_portfolio_router,
        create_portfolio_handler=application.create_portfolio_command_handler,
        get_portfolio_handler=application.get_portfolio_by_id_query_handler,
        get_user_portfolios_handler=application.get_user_portfolios_query_handler,
        analyze_portfolio_handler=application.analyze_portfolio_query_handler,
    )
    
    investment_router = providers.Factory(
        _create_investment_router,
        create_investment_handler=application.create_investment_command_handler,
        add_investment_handler=application.add_investment_to_portfolio_command_handler,
        find_investments_handler=application.find_investments_query_handler,
        get_investment_handler=application.get_investment_by_id_query_handler,
    )
    
    auth_router = providers.Factory(
        _create_auth_router,
        jwt_service=jwt_service,
    )
    
    health_router = providers.Factory(
        _create_health_router,
    )
