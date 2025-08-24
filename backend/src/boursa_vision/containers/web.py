"""
Web Container - FastAPI Integration and Web Layer
================================================

WebContainer manages all web-related components including FastAPI application,
routers, middleware, authentication, and HTTP-specific concerns. This container
integrates with dependency-injector's wiring system for clean separation.

Features:
- FastAPI application factory with proper DI wiring
- Router registration and middleware configuration
- Authentication and authorization components
- Request/response handling and serialization
- Error handling and logging middleware

Dependencies: ApplicationContainer for CQRS handlers, InfrastructureContainer
"""

from dependency_injector import containers, providers


class WebContainer(containers.DeclarativeContainer):
    """
    Web container for FastAPI application and HTTP layer components.
    
    Contains:
        - FastAPI application factory with dependency injection
        - Router modules and endpoint handlers
        - Authentication and security middleware
        - Request/response serialization components
        - Error handling and logging middleware
    
    This container integrates the Clean Architecture with FastAPI,
    providing proper dependency injection through wiring system.
    """
    
    # Dependencies from other containers
    application = providers.DependenciesContainer()
    infrastructure = providers.DependenciesContainer()
    
    # =============================================================================
    # FASTAPI APPLICATION AND CONFIGURATION
    # =============================================================================
    
    fastapi_app = providers.Factory(
        _create_fastapi_app,
        config=infrastructure.config,
        logger=infrastructure.logger,
    )
    
    # =============================================================================
    # AUTHENTICATION AND SECURITY COMPONENTS
    # =============================================================================
    
    auth_middleware = providers.Factory(
        _create_auth_middleware,
        jwt_service=infrastructure.jwt_service,
        rate_limiter=infrastructure.rate_limiter,
        logger=infrastructure.logger,
    )
    
    cors_middleware = providers.Factory(
        _create_cors_middleware,
        config=infrastructure.config,
    )
    
    security_headers_middleware = providers.Factory(
        _create_security_headers_middleware,
        config=infrastructure.config,
    )
    
    # =============================================================================
    # REQUEST/RESPONSE HANDLING
    # =============================================================================
    
    request_validator = providers.Factory(
        _create_request_validator,
        logger=infrastructure.logger,
    )
    
    response_serializer = providers.Factory(
        _create_response_serializer,
        logger=infrastructure.logger,
    )
    
    error_handler = providers.Factory(
        _create_error_handler,
        logger=infrastructure.logger,
        metrics_collector=infrastructure.metrics_collector,
    )
    
    # =============================================================================
    # API ROUTERS AND ENDPOINTS
    # =============================================================================
    
    auth_router = providers.Factory(
        _create_auth_router,
        register_handler=application.register_user_command_handler,
        jwt_service=infrastructure.jwt_service,
        logger=infrastructure.logger,
    )
    
    portfolio_router = providers.Factory(
        _create_portfolio_router,
        create_handler=application.create_portfolio_command_handler,
        update_handler=application.update_portfolio_command_handler,
        delete_handler=application.delete_portfolio_command_handler,
        get_handler=application.get_portfolio_query_handler,
        list_handler=application.get_user_portfolios_query_handler,
        performance_handler=application.get_portfolio_performance_handler,
        auth_middleware=auth_middleware,
        logger=infrastructure.logger,
    )
    
    investment_router = providers.Factory(
        _create_investment_router,
        add_handler=application.add_investment_command_handler,
        remove_handler=application.remove_investment_command_handler,
        update_handler=application.update_investment_command_handler,
        details_handler=application.get_investment_details_handler,
        search_handler=application.search_investments_query_handler,
        auth_middleware=auth_middleware,
        logger=infrastructure.logger,
    )
    
    transaction_router = providers.Factory(
        _create_transaction_router,
        buy_handler=application.execute_buy_transaction_handler,
        sell_handler=application.execute_sell_transaction_handler,
        auth_middleware=auth_middleware,
        logger=infrastructure.logger,
    )
    
    market_data_router = providers.Factory(
        _create_market_data_router,
        overview_handler=application.get_market_overview_handler,
        price_history_handler=application.get_price_history_handler,
        signals_handler=application.get_market_signals_handler,
        auth_middleware=auth_middleware,
        logger=infrastructure.logger,
    )
    
    analytics_router = providers.Factory(
        _create_analytics_router,
        risk_analysis_handler=application.get_risk_analysis_handler,
        performance_metrics_handler=application.get_performance_metrics_handler,
        auth_middleware=auth_middleware,
        logger=infrastructure.logger,
    )
    
    # =============================================================================
    # WEBSOCKET HANDLERS - Real-time features
    # =============================================================================
    
    market_websocket_handler = providers.Factory(
        _create_market_websocket_handler,
        market_data_service=infrastructure.market_data_service,
        redis_pubsub=infrastructure.redis_pubsub_client,
        auth_middleware=auth_middleware,
        logger=infrastructure.logger,
    )
    
    portfolio_websocket_handler = providers.Factory(
        _create_portfolio_websocket_handler,
        performance_handler=application.get_portfolio_performance_handler,
        redis_pubsub=infrastructure.redis_pubsub_client,
        auth_middleware=auth_middleware,
        logger=infrastructure.logger,
    )
    
    # =============================================================================
    # HEALTH CHECK AND MONITORING ENDPOINTS
    # =============================================================================
    
    health_router = providers.Factory(
        _create_health_router,
        health_check_service=infrastructure.health_check_service,
        metrics_collector=infrastructure.metrics_collector,
    )
    
    metrics_router = providers.Factory(
        _create_metrics_router,
        metrics_collector=infrastructure.metrics_collector,
        auth_middleware=auth_middleware,
    )


# =============================================================================
# FASTAPI APPLICATION FACTORY FUNCTIONS
# =============================================================================

def _create_fastapi_app(config, logger):
    """Create FastAPI application with proper configuration and middleware."""
    from boursa_vision.web.app_factory import create_fastapi_app
    return create_fastapi_app(
        title=config.api.title,
        description=config.api.description,
        version=config.api.version,
        debug=config.api.debug,
        docs_url=config.api.docs_url,
        redoc_url=config.api.redoc_url,
        openapi_url=config.api.openapi_url,
        logger=logger,
    )


# =============================================================================
# MIDDLEWARE FACTORY FUNCTIONS
# =============================================================================

def _create_auth_middleware(jwt_service, rate_limiter, logger):
    """Create authentication and authorization middleware."""
    from boursa_vision.web.middleware.auth_middleware import AuthMiddleware
    return AuthMiddleware(
        jwt_service=jwt_service,
        rate_limiter=rate_limiter,
        logger=logger,
    )


def _create_cors_middleware(config):
    """Create CORS middleware for cross-origin requests."""
    from boursa_vision.web.middleware.cors_middleware import create_cors_middleware
    return create_cors_middleware(
        allowed_origins=config.cors.allowed_origins,
        allowed_methods=config.cors.allowed_methods,
        allowed_headers=config.cors.allowed_headers,
        allow_credentials=config.cors.allow_credentials,
    )


def _create_security_headers_middleware(config):
    """Create security headers middleware."""
    from boursa_vision.web.middleware.security_middleware import SecurityHeadersMiddleware
    return SecurityHeadersMiddleware(
        hsts_max_age=config.security.hsts_max_age,
        content_security_policy=config.security.content_security_policy,
    )


# =============================================================================
# REQUEST/RESPONSE HANDLING FACTORY FUNCTIONS
# =============================================================================

def _create_request_validator(logger):
    """Create request validation component."""
    from boursa_vision.web.validation.request_validator import RequestValidator
    return RequestValidator(logger=logger)


def _create_response_serializer(logger):
    """Create response serialization component."""
    from boursa_vision.web.serialization.response_serializer import ResponseSerializer
    return ResponseSerializer(logger=logger)


def _create_error_handler(logger, metrics_collector):
    """Create centralized error handling component."""
    from boursa_vision.web.error_handling.error_handler import ErrorHandler
    return ErrorHandler(
        logger=logger,
        metrics_collector=metrics_collector,
    )


# =============================================================================
# ROUTER FACTORY FUNCTIONS
# =============================================================================

def _create_auth_router(register_handler, jwt_service, logger):
    """Create authentication router with login/logout endpoints."""
    from boursa_vision.web.routers.auth_router import create_auth_router
    return create_auth_router(
        register_handler=register_handler,
        jwt_service=jwt_service,
        logger=logger,
    )


def _create_portfolio_router(create_handler, update_handler, delete_handler, get_handler, list_handler, performance_handler, auth_middleware, logger):
    """Create portfolio management router."""
    from boursa_vision.web.routers.portfolio_router import create_portfolio_router
    return create_portfolio_router(
        create_handler=create_handler,
        update_handler=update_handler,
        delete_handler=delete_handler,
        get_handler=get_handler,
        list_handler=list_handler,
        performance_handler=performance_handler,
        auth_middleware=auth_middleware,
        logger=logger,
    )


def _create_investment_router(add_handler, remove_handler, update_handler, details_handler, search_handler, auth_middleware, logger):
    """Create investment management router."""
    from boursa_vision.web.routers.investment_router import create_investment_router
    return create_investment_router(
        add_handler=add_handler,
        remove_handler=remove_handler,
        update_handler=update_handler,
        details_handler=details_handler,
        search_handler=search_handler,
        auth_middleware=auth_middleware,
        logger=logger,
    )


def _create_transaction_router(buy_handler, sell_handler, auth_middleware, logger):
    """Create transaction execution router."""
    from boursa_vision.web.routers.transaction_router import create_transaction_router
    return create_transaction_router(
        buy_handler=buy_handler,
        sell_handler=sell_handler,
        auth_middleware=auth_middleware,
        logger=logger,
    )


def _create_market_data_router(overview_handler, price_history_handler, signals_handler, auth_middleware, logger):
    """Create market data router."""
    from boursa_vision.web.routers.market_data_router import create_market_data_router
    return create_market_data_router(
        overview_handler=overview_handler,
        price_history_handler=price_history_handler,
        signals_handler=signals_handler,
        auth_middleware=auth_middleware,
        logger=logger,
    )


def _create_analytics_router(risk_analysis_handler, performance_metrics_handler, auth_middleware, logger):
    """Create analytics and reporting router."""
    from boursa_vision.web.routers.analytics_router import create_analytics_router
    return create_analytics_router(
        risk_analysis_handler=risk_analysis_handler,
        performance_metrics_handler=performance_metrics_handler,
        auth_middleware=auth_middleware,
        logger=logger,
    )


# =============================================================================
# WEBSOCKET HANDLER FACTORY FUNCTIONS
# =============================================================================

def _create_market_websocket_handler(market_data_service, redis_pubsub, auth_middleware, logger):
    """Create WebSocket handler for real-time market data."""
    from boursa_vision.web.websockets.market_websocket_handler import MarketWebSocketHandler
    return MarketWebSocketHandler(
        market_data_service=market_data_service,
        redis_pubsub=redis_pubsub,
        auth_middleware=auth_middleware,
        logger=logger,
    )


def _create_portfolio_websocket_handler(performance_handler, redis_pubsub, auth_middleware, logger):
    """Create WebSocket handler for real-time portfolio updates."""
    from boursa_vision.web.websockets.portfolio_websocket_handler import PortfolioWebSocketHandler
    return PortfolioWebSocketHandler(
        performance_handler=performance_handler,
        redis_pubsub=redis_pubsub,
        auth_middleware=auth_middleware,
        logger=logger,
    )


# =============================================================================
# MONITORING ROUTER FACTORY FUNCTIONS
# =============================================================================

def _create_health_router(health_check_service, metrics_collector):
    """Create health check router for monitoring."""
    from boursa_vision.web.routers.health_router import create_health_router
    return create_health_router(
        health_check_service=health_check_service,
        metrics_collector=metrics_collector,
    )


def _create_metrics_router(metrics_collector, auth_middleware):
    """Create metrics router for Prometheus/monitoring."""
    from boursa_vision.web.routers.metrics_router import create_metrics_router
    return create_metrics_router(
        metrics_collector=metrics_collector,
        auth_middleware=auth_middleware,
    )
