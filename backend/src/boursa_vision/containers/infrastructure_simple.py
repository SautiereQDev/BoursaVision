"""
Infrastructure Container - External Services Integration (Simplified)
==================================================================

InfrastructureContainer manages external services and integrations.
This simplified version focuses on core infrastructure needed for
the application to function.

Features:
- Mock implementations for external services
- Basic configuration management
- Simple service factories

Dependencies: CoreContainer
"""

from dependency_injector import containers, providers


# =============================================================================
# INFRASTRUCTURE FACTORY FUNCTIONS
# =============================================================================

def _create_redis_client(url):
    """Create mock Redis client for Phase 1."""
    class MockRedisClient:
        def __init__(self, url):
            self.url = url
            self._data = {}
        
        def get(self, key):
            return self._data.get(key)
        
        def set(self, key, value, ex=None):
            self._data[key] = value
            return True
        
        def delete(self, *keys):
            deleted = 0
            for key in keys:
                if key in self._data:
                    del self._data[key]
                    deleted += 1
            return deleted
        
        def ping(self):
            return True
    
    return MockRedisClient(url)


def _create_cache_service(redis_client):
    """Create mock cache service."""
    class MockCacheService:
        def __init__(self, redis_client):
            self.redis_client = redis_client
        
        def get(self, key):
            return self.redis_client.get(key)
        
        def set(self, key, value, ttl=None):
            return self.redis_client.set(key, value, ex=ttl)
        
        def delete(self, *keys):
            return self.redis_client.delete(*keys)
    
    return MockCacheService(redis_client)


def _create_celery_app(broker_url, result_backend):
    """Create mock Celery app for Phase 1."""
    class MockCeleryApp:
        def __init__(self, broker_url, result_backend):
            self.broker_url = broker_url
            self.result_backend = result_backend
        
        def task(self, func):
            # Mock decorator that just returns the function
            return func
    
    return MockCeleryApp(broker_url, result_backend)


def _create_task_scheduler(celery_app):
    """Create mock task scheduler."""
    class MockTaskScheduler:
        def __init__(self, celery_app):
            self.celery_app = celery_app
        
        def schedule(self, task_name, *args, **kwargs):
            print(f"Mock: Scheduling task {task_name} with args {args}, kwargs {kwargs}")
    
    return MockTaskScheduler(celery_app)


def _create_yfinance_client(cache_service):
    """Create mock YFinance client."""
    class MockYFinanceClient:
        def __init__(self, cache_service):
            self.cache_service = cache_service
        
        def get_stock_price(self, symbol):
            # Mock implementation
            return 100.0
        
        def get_historical_data(self, symbol, period="1y"):
            # Mock implementation
            return []
    
    return MockYFinanceClient(cache_service)


def _create_market_data_service(yfinance_client, cache_service):
    """Create mock market data service."""
    class MockMarketDataService:
        def __init__(self, yfinance_client, cache_service):
            self.yfinance_client = yfinance_client
            self.cache_service = cache_service
        
        def get_current_price(self, symbol):
            return self.yfinance_client.get_stock_price(symbol)
        
        def get_price_history(self, symbol, period="1y"):
            return self.yfinance_client.get_historical_data(symbol, period)
    
    return MockMarketDataService(yfinance_client, cache_service)


def _create_email_service(smtp_host, smtp_port, smtp_username, smtp_password):
    """Create mock email service."""
    class MockEmailService:
        def __init__(self, smtp_host, smtp_port, smtp_username, smtp_password):
            self.smtp_host = smtp_host
            self.smtp_port = smtp_port
            self.smtp_username = smtp_username
        
        def send_email(self, to, subject, body):
            print(f"Mock: Sending email to {to}: {subject}")
            return True
    
    return MockEmailService(smtp_host, smtp_port, smtp_username, smtp_password)


def _create_notification_service(email_service):
    """Create mock notification service."""
    class MockNotificationService:
        def __init__(self, email_service):
            self.email_service = email_service
        
        def send_notification(self, user_id, message, channel="email"):
            print(f"Mock: Sending notification to user {user_id}: {message}")
            return True
    
    return MockNotificationService(email_service)


# =============================================================================
# INFRASTRUCTURE CONTAINER CLASS
# =============================================================================

class InfrastructureContainer(containers.DeclarativeContainer):
    """
    Infrastructure container for external services (simplified).
    
    Contains:
        - Mock Redis cache for performance optimization
        - Mock background task management (Celery)
        - Mock email and notification services
        - Mock external API clients (YFinance, etc.)
        - Configuration and settings management
        - Mock health check and monitoring services
    
    This layer provides technical infrastructure supporting
    the application's non-functional requirements.
    """
    
    # Dependencies from other containers
    core = providers.DependenciesContainer()
    
    # =============================================================================
    # REDIS CACHE SERVICES
    # =============================================================================
    
    redis_client = providers.Singleton(
        _create_redis_client,
        url=core.config.redis_url,
    )
    
    cache_service = providers.Factory(
        _create_cache_service,
        redis_client=redis_client,
    )
    
    # =============================================================================
    # BACKGROUND TASK SERVICES
    # =============================================================================
    
    celery_app = providers.Singleton(
        _create_celery_app,
        broker_url=core.config.celery_broker_url,
        result_backend=core.config.celery_result_backend,
    )
    
    task_scheduler = providers.Factory(
        _create_task_scheduler,
        celery_app=celery_app,
    )
    
    # =============================================================================
    # EXTERNAL API SERVICES
    # =============================================================================
    
    yfinance_client = providers.Factory(
        _create_yfinance_client,
        cache_service=cache_service,
    )
    
    market_data_service = providers.Factory(
        _create_market_data_service,
        yfinance_client=yfinance_client,
        cache_service=cache_service,
    )
    
    # =============================================================================
    # NOTIFICATION SERVICES
    # =============================================================================
    
    email_service = providers.Factory(
        _create_email_service,
        smtp_host=core.config.smtp_host,
        smtp_port=core.config.smtp_port,
        smtp_username=core.config.smtp_username,
        smtp_password=core.config.smtp_password,
    )
    
    notification_service = providers.Factory(
        _create_notification_service,
        email_service=email_service,
    )
