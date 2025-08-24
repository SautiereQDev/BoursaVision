"""
Core Container - Foundation of Dependency Injection System
=========================================================

CoreContainer handles the fundamental infrastructure of the application:
- Multi-source configuration management (YAML, ENV, validation)
- Structured logging with environment-specific levels
- Metrics and monitoring (Prometheus integration)
- Feature flags for runtime behavior control

This container has no dependencies and serves as the foundation for all other containers.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any

from dependency_injector import containers, providers
from dependency_injector.providers import Configuration


def _get_log_level_for_environment(environment: str) -> str:
    """Get appropriate log level based on environment."""
    levels = {
        "production": "INFO",
        "staging": "INFO", 
        "development": "DEBUG",
        "testing": "WARNING",
    }
    return levels.get(environment, "INFO")


def _create_structured_logger(level: str, environment: str):
    """Create structured logger with appropriate configuration."""
    import logging
    from logging.config import dictConfig
    
    # Configure structured logging
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(levelname)s - %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured" if environment != "development" else "simple",
                "level": level,
            }
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
        "loggers": {
            "boursa_vision": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            }
        }
    }
    
    dictConfig(config)
    return logging.getLogger("boursa_vision")


def _create_metrics_client(enabled: bool, environment: str):
    """Create metrics client (placeholder implementation)."""
    class MockMetricsClient:
        def __init__(self):
            self.enabled = enabled
            
        def increment(self, metric, tags=None):
            if self.enabled:
                print(f"METRIC: {metric} +1 {tags or {}}")
        
        def gauge(self, metric, value, tags=None):
            if self.enabled:
                print(f"METRIC: {metric} = {value} {tags or {}}")
    
    return MockMetricsClient()


def _create_feature_flags_service(config, environment: str):
    """Create feature flags service (placeholder implementation)."""
    class MockFeatureFlagsService:
        def __init__(self):
            self.flags = getattr(config, 'flags', {})
        
        def is_enabled(self, flag_name: str) -> bool:
            return self.flags.get(flag_name, False)
        
        def get_variant(self, flag_name: str, default="default"):
            return self.flags.get(f"{flag_name}_variant", default)
    
    return MockFeatureFlagsService()


class CoreContainer(containers.DeclarativeContainer):
    """
    Core container for fundamental application infrastructure.
    
    Provides:
        - Configuration management with multi-source loading
        - Structured logging setup
        - Metrics collection (Prometheus)
        - Feature flags
        - Environment detection
    """
    
    # Configuration provider - Source of truth for all settings
    config = providers.Configuration()
    
    # Environment detection
    environment = providers.Singleton(
        lambda: os.getenv("ENVIRONMENT", "development")
    )
    
    # Logging configuration
    log_level = providers.Singleton(
        lambda env: _get_log_level_for_environment(env),
        env=environment,
    )
    
    # Structured logger factory
    logger = providers.Singleton(
        _create_structured_logger,
        level=log_level,
        environment=environment,
    )
    
    # Metrics client (Prometheus compatible)
    metrics_client = providers.Singleton(
        _create_metrics_client,
        enabled=config.monitoring.metrics_enabled.as_(bool, default=True),
        environment=environment,
    )
    
        # Feature flags service
    feature_flags = providers.Singleton(
        _create_feature_flags_service,
        config=config.feature_flags,
        environment=environment,
    )


def _get_log_level_for_environment(environment: str) -> str:
    """Get appropriate log level based on environment."""
    levels = {
        "production": "INFO",
        "staging": "INFO", 
        "development": "DEBUG",
        "testing": "WARNING",
    }
    return levels.get(environment, "INFO")


def _create_structured_logger(level: str, environment: str) -> logging.Logger:
    """
    Create a structured logger with appropriate configuration.
    
    In production: JSON format for log aggregation
    In development: Human-readable format for debugging
    """
    logger = logging.getLogger("boursa_vision")
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set level
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Create formatter based on environment
    if environment == "production":
        # JSON formatter for production log aggregation
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s", '
            '"module": "%(module)s", "function": "%(funcName)s"}'
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for persistent logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / f"boursa_vision_{environment}.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def _create_metrics_client(enabled: bool, environment: str) -> "MetricsClient":
    """Create metrics client for monitoring and observability."""
    if not enabled or environment == "testing":
        return _NullMetricsClient()
    
    # In a real implementation, this would be Prometheus client
    return _MockMetricsClient(environment=environment)


def _create_feature_flags_service(config: Configuration, environment: str) -> "FeatureFlagsService":
    """Create feature flags service for runtime behavior control."""
    return _FeatureFlagsService(config=config, environment=environment)


# Mock implementations for the Phase 1 (will be replaced with real implementations later)

class _NullMetricsClient:
    """Null object pattern for disabled metrics."""
    
    def counter(self, name: str) -> "Counter":
        return _NullCounter()
    
    def histogram(self, name: str) -> "Histogram":
        return _NullHistogram()
    
    def gauge(self, name: str) -> "Gauge":
        return _NullGauge()


class _NullCounter:
    def inc(self, value: float = 1.0) -> None:
        pass


class _NullHistogram:
    def observe(self, value: float) -> None:
        pass


class _NullGauge:
    def set(self, value: float) -> None:
        pass


class _MockMetricsClient:
    """Mock metrics client for development/staging."""
    
    def __init__(self, environment: str):
        self.environment = environment
        self._metrics: Dict[str, float] = {}
    
    def counter(self, name: str) -> "MockCounter":
        return _MockCounter(name, self._metrics)
    
    def histogram(self, name: str) -> "MockHistogram":
        return _MockHistogram(name, self._metrics)
    
    def gauge(self, name: str) -> "MockGauge":
        return _MockGauge(name, self._metrics)


class _MockCounter:
    def __init__(self, name: str, metrics: Dict[str, float]):
        self.name = name
        self.metrics = metrics
    
    def inc(self, value: float = 1.0) -> None:
        self.metrics[self.name] = self.metrics.get(self.name, 0) + value


class _MockHistogram:
    def __init__(self, name: str, metrics: Dict[str, float]):
        self.name = name
        self.metrics = metrics
    
    def observe(self, value: float) -> None:
        self.metrics[f"{self.name}_latest"] = value


class _MockGauge:
    def __init__(self, name: str, metrics: Dict[str, float]):
        self.name = name
        self.metrics = metrics
    
    def set(self, value: float) -> None:
        self.metrics[self.name] = value


class _FeatureFlagsService:
    """Feature flags service for runtime behavior control."""
    
    def __init__(self, config: Configuration, environment: str):
        self.config = config
        self.environment = environment
        self._flags: Dict[str, Any] = {}
    
    def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled."""
        # Try to get from config first, then default
        try:
            return bool(self.config.get(flag_name, default))
        except Exception:
            return default
    
    def get_value(self, flag_name: str, default: Any = None) -> Any:
        """Get feature flag value."""
        try:
            return self.config.get(flag_name, default)
        except Exception:
            return default
