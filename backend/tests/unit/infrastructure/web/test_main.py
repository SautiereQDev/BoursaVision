"""
Tests for FastAPI Main Application
==================================

Comprehensive tests for main.py covering:
- Application creation and configuration
- Middleware setup
- Exception handlers
- Router inclusion
- Health checks and root endpoints
- Lifespan events
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boursa_vision.infrastructure.web.main import create_application, app, lifespan


class TestApplicationCreation:
    """Test application creation and configuration."""

    def test_create_application_returns_fastapi_instance(self):
        """Test that create_application returns a FastAPI instance."""
        application = create_application()
        assert isinstance(application, FastAPI)

    def test_application_has_correct_title(self):
        """Test application title configuration."""
        application = create_application()
        assert "Boursa Vision" in application.title

    def test_application_has_routes(self):
        """Test that application includes expected routes."""
        application = create_application()
        route_paths = [route.path for route in application.routes]
        
        # Check for expected routes
        assert "/" in route_paths
        assert "/health" in route_paths

    @patch("boursa_vision.infrastructure.web.main.settings")
    def test_application_middleware_configuration(self, mock_settings):
        """Test middleware stack configuration."""
        mock_settings.rate_limit_enabled = True
        mock_settings.rate_limit_calls = 100
        mock_settings.rate_limit_period = 60
        mock_settings.cors_origins = ["*"]
        mock_settings.cors_methods = ["GET", "POST"]
        mock_settings.cors_headers = ["*"]
        mock_settings.environment = "development"
        
        application = create_application()
        
        # Verify middleware stack is applied
        assert len(application.user_middleware) > 0

    @patch("boursa_vision.infrastructure.web.main.settings")
    def test_production_configuration(self, mock_settings):
        """Test production environment configuration."""
        mock_settings.environment = "production"
        mock_settings.app_name = "Boursa Vision API"
        mock_settings.app_description = "Investment API"
        mock_settings.app_version = "1.0.0"
        mock_settings.debug = False
        mock_settings.rate_limit_enabled = False
        mock_settings.cors_origins = []
        mock_settings.cors_methods = []
        mock_settings.cors_headers = []
        
        application = create_application()
        
        # In production, docs should be disabled
        assert application.openapi_url is None
        assert application.docs_url is None
        assert application.redoc_url is None

    @patch("boursa_vision.infrastructure.web.main.settings")
    def test_development_configuration(self, mock_settings):
        """Test development environment configuration."""
        mock_settings.environment = "development"
        mock_settings.app_name = "Boursa Vision API"
        mock_settings.app_description = "Investment API"
        mock_settings.app_version = "1.0.0"
        mock_settings.debug = True
        mock_settings.rate_limit_enabled = True
        mock_settings.rate_limit_calls = 100
        mock_settings.rate_limit_period = 60
        mock_settings.cors_origins = ["*"]
        mock_settings.cors_methods = ["GET", "POST"]
        mock_settings.cors_headers = ["*"]
        
        application = create_application()
        
        # In development, docs should be enabled
        assert application.openapi_url is not None
        assert application.docs_url is not None
        assert application.redoc_url is not None


class TestApplicationEndpoints:
    """Test application endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint response."""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "version" in data
            assert "environment" in data
            assert data["message"] == "Boursa Vision API"

    def test_health_endpoint(self):
        """Test health check endpoint."""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "boursa-vision-api"
            assert "version" in data
            assert "environment" in data
            assert "timestamp" in data

    def test_404_endpoint(self):
        """Test non-existent endpoint returns 404."""
        with TestClient(app) as client:
            response = client.get("/nonexistent")
            assert response.status_code == 404


class TestLifespanEvents:
    """Test application lifespan events."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(self):
        """Test lifespan startup and shutdown events."""
        mock_app = Mock()
        
        # Test lifespan context manager
        async with lifespan(mock_app) as context:
            # Startup completed successfully
            assert context is None  # lifespan yields None
        
        # Shutdown completed successfully (no exceptions raised)

    @pytest.mark.asyncio
    @patch("boursa_vision.infrastructure.web.main.logger")
    async def test_lifespan_logging(self, mock_logger):
        """Test that lifespan events are logged."""
        mock_app = Mock()
        
        async with lifespan(mock_app):
            pass
        
        # Verify startup and shutdown logs were called
        mock_logger.info.assert_called()
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]
        
        startup_logged = any("Starting Boursa Vision API" in arg for arg in call_args)
        shutdown_logged = any("Shutting down Boursa Vision API" in arg for arg in call_args)
        
        assert startup_logged
        assert shutdown_logged


class TestApplicationInstance:
    """Test the global application instance."""

    def test_app_instance_is_fastapi(self):
        """Test that the global app instance is a FastAPI application."""
        assert isinstance(app, FastAPI)

    def test_app_has_expected_properties(self):
        """Test that the app instance has expected properties."""
        assert hasattr(app, 'title')
        assert hasattr(app, 'version')
        assert hasattr(app, 'routes')
        assert hasattr(app, 'middleware')


class TestExceptionHandlers:
    """Test exception handler configuration."""

    def test_api_exception_handler_registered(self):
        """Test that API exception handler is registered."""
        application = create_application()
        # Check that exception handlers are configured
        assert len(application.exception_handlers) > 0

    def test_validation_exception_handler_registered(self):
        """Test that validation exception handler is registered."""
        from fastapi.exceptions import RequestValidationError
        application = create_application()
        # Verify RequestValidationError handler exists
        assert RequestValidationError in application.exception_handlers

    def test_general_exception_handler_registered(self):
        """Test that general exception handler is registered."""
        application = create_application()
        # Verify Exception handler exists
        assert Exception in application.exception_handlers


class TestRouterInclusion:
    """Test router inclusion and configuration."""

    def test_routers_are_included(self):
        """Test that expected routers are included."""
        application = create_application()
        
        # Get all router prefixes/tags from routes
        route_paths = [route.path for route in application.routes if hasattr(route, 'path')]
        
        # Check that routes from different routers exist
        # (This is a basic check - specific route testing should be in router tests)
        assert len(route_paths) > 2  # At least root, health, and router paths

    def test_openapi_tags_configuration(self):
        """Test OpenAPI tags configuration."""
        application = create_application()
        
        expected_tags = ["portfolios", "investments", "market-data", "websocket"]
        
        if application.openapi_tags:
            configured_tags = [tag["name"] for tag in application.openapi_tags]
            for tag in expected_tags:
                assert tag in configured_tags


def test_main_module_executable():
    """Test that main module can be executed."""
    import boursa_vision.infrastructure.web.main as main_module
    
    # Test that the module has the expected components
    assert hasattr(main_module, 'app')
    assert hasattr(main_module, 'create_application')
    assert hasattr(main_module, 'lifespan')
    
    # Test that app is properly configured
    assert main_module.app.title is not None
    assert main_module.app.version is not None
