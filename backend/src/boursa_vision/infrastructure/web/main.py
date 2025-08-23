"""
FastAPI Main Application
=======================

Comprehensive FastAPI application for Boursa Vision with:
- API versioning
- Middleware stack
- Global error handling
- OpenAPI documentation
- WebSocket support
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .error_handlers import (
    api_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)
from .exceptions import APIException
from .middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from .routers import auth, investments, market_data, portfolio, websocket

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Boursa Vision API", version=settings.app_version)

    # TODO: Initialize database connections, cache, etc.
    # await initialize_database()
    # await initialize_cache()
    # await start_background_tasks()

    logger.info("API startup completed")

    yield

    # Shutdown
    logger.info("Shutting down Boursa Vision API")

    # TODO: Cleanup connections, stop background tasks, etc.
    # await cleanup_database()
    # await cleanup_cache()
    # await stop_background_tasks()

    logger.info("API shutdown completed")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Create FastAPI application with comprehensive configuration
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        openapi_url="/api/v1/openapi.json"
        if settings.environment != "production"
        else None,
        docs_url="/api/v1/docs" if settings.environment != "production" else None,
        redoc_url="/api/v1/redoc" if settings.environment != "production" else None,
        openapi_tags=[
            {
                "name": "portfolios",
                "description": "Portfolio management operations",
            },
            {
                "name": "investments",
                "description": "Investment recommendations and analysis",
            },
            {
                "name": "market-data",
                "description": "Market data and financial information",
            },
            {
                "name": "websocket",
                "description": "Real-time WebSocket communication",
            },
        ],
    )

    # Add middleware stack (order matters!)
    if settings.rate_limit_enabled:
        application.add_middleware(
            RateLimitMiddleware,
            calls=settings.rate_limit_calls,
            period=settings.rate_limit_period,
        )

    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(LoggingMiddleware)

    # CORS Configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Add global exception handlers
    application.add_exception_handler(APIException, api_exception_handler)
    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    application.add_exception_handler(Exception, general_exception_handler)

    # TODO: Add domain exception handlers when domain layer is ready
    # application.add_exception_handler(DomainError, domain_exception_handler)
    # application.add_exception_handler(BusinessLogicError, domain_exception_handler)

    # Include routers with API versioning
    application.include_router(portfolio.router)
    application.include_router(investments.router)
    application.include_router(market_data.router)
    application.include_router(auth.router)
    # application.include_router(websocket.router)  # Keep commented for now

    # Root endpoints
    @application.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Boursa Vision API",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "docs_url": "/api/v1/docs"
            if settings.environment != "production"
            else None,
            "health_url": "/health",
        }

    @application.get("/health", tags=["health"])
    async def health_check():
        """Comprehensive health check endpoint."""
        return {
            "status": "healthy",
            "service": "boursa-vision-api",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "timestamp": "2024-01-01T00:00:00Z",
            # TODO: Add actual health checks
            # "database": await check_database_health(),
            # "cache": await check_cache_health(),
            # "external_services": await check_external_services_health(),
        }

    return application


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info" if not settings.debug else "debug",
    )
