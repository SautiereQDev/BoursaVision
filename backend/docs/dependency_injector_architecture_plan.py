"""
🏗️ DEPENDENCY INJECTOR ARCHITECTURE REFACTORING PLAN
=====================================================

Cette document détaille l'architecture complète pour une refonte totale
de BoursaVision utilisant pleinement dependency-injector v4.48.1.

🎯 OBJECTIFS:
- Utiliser pleinement le potentiel de dependency-injector
- Respecter les conventions et bonnes pratiques
- Maintenir la Clean Architecture
- Optimiser la testabilité et la maintenabilité
"""

# ========================================
# 🏛️ ARCHITECTURE MODULAIRE DES CONTAINERS
# ========================================

"""
📁 Structure proposée:

backend/src/boursa_vision/
├── containers/                         # 🆕 Nouveau dossier containers
│   ├── __init__.py                    # Exports principaux
│   ├── core.py                        # CoreContainer (config, logging)
│   ├── database.py                    # DatabaseContainer (sessions, connections)
│   ├── repositories.py                # RepositoryContainer (tous les repos)
│   ├── services.py                    # ServiceContainer (domain services)  
│   ├── application.py                 # ApplicationContainer (use cases)
│   ├── infrastructure.py              # InfrastructureContainer (APIs, clients)
│   ├── web.py                         # WebContainer (FastAPI deps)
│   └── main.py                        # MainContainer (composition finale)
├── domain/                            # ✅ Inchangé
├── application/                       # 🔄 Modifié pour DI
└── infrastructure/                    # 🔄 Modifié pour DI
"""

# ========================================
# 🔧 1. CORE CONTAINER
# ========================================

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide

class CoreContainer(containers.DeclarativeContainer):
    """Container de base: configuration, logging, monitoring"""
    
    # Configuration provider - Source de vérité unique
    config = providers.Configuration()
    
    # Logging provider avec configuration environnement
    logger = providers.Resource(
        create_structured_logger,
        level=config.logging.level,
        format=config.logging.format,
        output_file=config.logging.file,
    )
    
    # Monitoring et métriques
    metrics_client = providers.Singleton(
        PrometheusMetricsClient,
        enabled=config.monitoring.metrics_enabled.as_(bool),
        push_gateway=config.monitoring.push_gateway,
    )
    
    # Feature flags provider
    feature_flags = providers.Singleton(
        FeatureFlagsService,
        config=config.feature_flags,
    )


# ========================================
# 🗄️ 2. DATABASE CONTAINER
# ========================================

class DatabaseContainer(containers.DeclarativeContainer):
    """Container pour la gestion des bases de données"""
    
    config = providers.Configuration()
    
    # Connection pool principal (PostgreSQL)
    database_engine = providers.Resource(
        create_async_database_engine,
        url=config.database.url,
        pool_size=config.database.pool_size.as_(int),
        max_overflow=config.database.max_overflow.as_(int),
        pool_timeout=config.database.pool_timeout.as_(int),
        pool_recycle=config.database.pool_recycle.as_(int),
        echo=config.database.echo.as_(bool),
    )
    
    # Session factory
    session_factory = providers.Factory(
        create_async_session,
        bind=database_engine,
    )
    
    # TimescaleDB connection pour les données de marché
    timeseries_engine = providers.Resource(
        create_timescaledb_engine,
        url=config.timescaledb.url,
        pool_size=config.timescaledb.pool_size.as_(int),
    )
    
    # Redis connections avec différents rôles
    redis_cache = providers.Resource(
        create_redis_connection,
        url=config.redis.cache_url,
        decode_responses=True,
        max_connections=config.redis.max_connections.as_(int),
    )
    
    redis_session = providers.Resource(
        create_redis_connection,
        url=config.redis.session_url,
        decode_responses=False,  # Pour les sessions binaires
        max_connections=config.redis.max_connections.as_(int),
    )
    
    redis_pubsub = providers.Resource(
        create_redis_connection,
        url=config.redis.pubsub_url,
        decode_responses=True,
    )


# ========================================
# 📚 3. REPOSITORY CONTAINER
# ========================================

class RepositoryContainer(containers.DeclarativeContainer):
    """Container pour tous les repositories"""
    
    # Dependencies injectées depuis DatabaseContainer
    database = providers.DependenciesContainer()
    
    # Domain repositories (Clean Architecture compliant)
    user_repository = providers.Factory(
        SQLAlchemyUserRepository,
        session_factory=database.session_factory,
    )
    
    portfolio_repository = providers.Factory(
        SQLAlchemyPortfolioRepository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
    
    investment_repository = providers.Factory(
        SQLAlchemyInvestmentRepository,
        session_factory=database.session_factory,
    )
    
    # Market data avec TimescaleDB
    market_data_repository = providers.Factory(
        TimescaleMarketDataRepository,
        session_factory=database.session_factory,
        timeseries_engine=database.timeseries_engine,
        cache_client=database.redis_cache,
    )
    
    # Repositories d'infrastructure
    refresh_token_repository = providers.Factory(
        SQLAlchemyRefreshTokenRepository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
    
    notification_repository = providers.Factory(
        SQLAlchemyNotificationRepository,
        session_factory=database.session_factory,
    )


# ========================================
# 🎯 4. SERVICES CONTAINER (Domain Layer)
# ========================================

class ServicesContainer(containers.DeclarativeContainer):
    """Container pour les services métier (Domain Layer)"""
    
    repositories = providers.DependenciesContainer()
    
    # Domain Services purs (sans dépendances externes)
    risk_calculator = providers.Factory(
        RiskCalculatorService,
    )
    
    performance_analyzer = providers.Factory(
        PerformanceAnalyzerService,
        risk_calculator=risk_calculator,
    )
    
    portfolio_optimization_service = providers.Factory(
        PortfolioOptimizationService,
        risk_calculator=risk_calculator,
        performance_analyzer=performance_analyzer,
    )
    
    # Services avec repositories (Application Services en fait)
    portfolio_service = providers.Factory(
        PortfolioService,
        repository=repositories.portfolio_repository,
        investment_repository=repositories.investment_repository,
        performance_analyzer=performance_analyzer,
        risk_calculator=risk_calculator,
    )
    
    market_analysis_service = providers.Factory(
        MarketAnalysisService,
        market_data_repository=repositories.market_data_repository,
        performance_analyzer=performance_analyzer,
    )


# ========================================
# 📋 5. APPLICATION CONTAINER (Use Cases)
# ========================================

class ApplicationContainer(containers.DeclarativeContainer):
    """Container pour les Use Cases et Application Services"""
    
    services = providers.DependenciesContainer()
    repositories = providers.DependenciesContainer()
    
    # Commands (CQRS Write Side)
    create_portfolio_command = providers.Factory(
        CreatePortfolioCommand,
        portfolio_service=services.portfolio_service,
        user_repository=repositories.user_repository,
    )
    
    add_investment_command = providers.Factory(
        AddInvestmentToPortfolioCommand,
        portfolio_service=services.portfolio_service,
        investment_repository=repositories.investment_repository,
    )
    
    # Queries (CQRS Read Side)
    get_portfolios_query = providers.Factory(
        GetUserPortfoliosQuery,
        portfolio_repository=repositories.portfolio_repository,
    )
    
    get_market_data_query = providers.Factory(
        GetMarketDataQuery,
        market_data_repository=repositories.market_data_repository,
    )
    
    # Application Services complexes
    portfolio_management_service = providers.Factory(
        PortfolioManagementService,
        create_command=create_portfolio_command,
        add_investment_command=add_investment_command,
        portfolio_query=get_portfolios_query,
    )
    
    # Authentication & Authorization
    authentication_service = providers.Factory(
        AuthenticationService,
        user_repository=repositories.user_repository,
        token_repository=repositories.refresh_token_repository,
        password_service=password_service,
        jwt_service=jwt_service,
    )
    
    authorization_service = providers.Factory(
        AuthorizationService,
        user_repository=repositories.user_repository,
    )


# ========================================
# 🌐 6. INFRASTRUCTURE CONTAINER
# ========================================

class InfrastructureContainer(containers.DeclarativeContainer):
    """Container pour les services d'infrastructure"""
    
    config = providers.Configuration()
    database = providers.DependenciesContainer()
    core = providers.DependenciesContainer()
    
    # External API clients avec sélection d'environnement
    yfinance_client = providers.Selector(
        config.environment,
        production=providers.Singleton(
            YFinanceAPIClient,
            api_key=config.yfinance.api_key,
            rate_limiter=providers.Factory(
                RateLimiter,
                calls_per_minute=config.yfinance.rate_limit.as_(int),
            ),
            cache_client=database.redis_cache,
            metrics_client=core.metrics_client,
        ),
        development=providers.Singleton(MockYFinanceClient),
        testing=providers.Singleton(MockYFinanceClient),
    )
    
    # Email service
    email_service = providers.Selector(
        config.environment,
        production=providers.Singleton(
            SMTPEmailService,
            smtp_server=config.email.smtp_server,
            username=config.email.username,
            password=config.email.password,
        ),
        development=providers.Singleton(ConsoleEmailService),
        testing=providers.Singleton(MockEmailService),
    )
    
    # Storage services
    file_storage_service = providers.Selector(
        config.storage.provider,
        s3=providers.Singleton(
            S3StorageService,
            bucket=config.storage.s3.bucket,
            region=config.storage.s3.region,
            access_key=config.storage.s3.access_key,
            secret_key=config.storage.s3.secret_key,
        ),
        local=providers.Singleton(
            LocalFileStorageService,
            base_path=config.storage.local.base_path,
        ),
    )
    
    # Security services
    password_service = providers.Singleton(
        BCryptPasswordService,
        rounds=config.security.bcrypt_rounds.as_(int),
    )
    
    jwt_service = providers.Singleton(
        JWTTokenService,
        secret_key=config.security.jwt_secret,
        algorithm=config.security.jwt_algorithm,
        access_token_expire_minutes=config.security.access_token_expire_minutes.as_(int),
        refresh_token_expire_days=config.security.refresh_token_expire_days.as_(int),
    )
    
    # Background tasks
    celery_app = providers.Resource(
        create_celery_app,
        broker_url=config.celery.broker_url,
        backend_url=config.celery.backend_url,
        task_serializer=config.celery.task_serializer,
        result_serializer=config.celery.result_serializer,
    )


# ========================================
# 🌍 7. WEB CONTAINER (FastAPI Layer)
# ========================================

class WebContainer(containers.DeclarativeContainer):
    """Container pour la couche web FastAPI"""
    
    application = providers.DependenciesContainer()
    infrastructure = providers.DependenciesContainer()
    
    # FastAPI app factory avec toute la configuration
    fastapi_app = providers.Singleton(
        create_fastapi_app,
        title="BoursaVision API",
        version="2.0.0",
        cors_origins=providers.Configuration().web.cors_origins,
        middleware_stack=providers.Factory(
            create_middleware_stack,
            auth_service=application.authentication_service,
            rate_limiter=providers.Factory(APIRateLimiter),
        ),
    )
    
    # WebSocket manager
    websocket_manager = providers.Singleton(
        WebSocketManager,
        redis_client=providers.DependenciesContainer().database.redis_pubsub,
    )
    
    # API Dependencies pour FastAPI
    current_user_dependency = providers.Factory(
        CurrentUserDependency,
        auth_service=application.authentication_service,
    )
    
    pagination_dependency = providers.Factory(
        PaginationDependency,
        max_limit=providers.Configuration().web.max_page_size.as_(int),
    )


# ========================================
# 🏛️ 8. MAIN CONTAINER (Composition finale)
# ========================================

class MainContainer(containers.DeclarativeContainer):
    """Container principal qui compose tous les autres"""
    
    # Configuration globale
    config = providers.Configuration()
    
    # Containers modulaires
    core = providers.Container(CoreContainer, config=config)
    
    database = providers.Container(
        DatabaseContainer,
        config=config,
    )
    
    repositories = providers.Container(
        RepositoryContainer,
        database=database,
    )
    
    services = providers.Container(
        ServicesContainer,
        repositories=repositories,
    )
    
    application = providers.Container(
        ApplicationContainer,
        services=services,
        repositories=repositories,
    )
    
    infrastructure = providers.Container(
        InfrastructureContainer,
        config=config,
        database=database,
        core=core,
    )
    
    web = providers.Container(
        WebContainer,
        application=application,
        infrastructure=infrastructure,
    )


# ========================================
# ⚙️ CONFIGURATION MANAGEMENT
# ========================================

def create_main_container() -> MainContainer:
    """Factory pour créer le container principal configuré"""
    container = MainContainer()
    
    # Configuration par couches (priorité décroissante)
    container.config.from_yaml("config/base.yml")
    container.config.from_yaml(f"config/{os.getenv('ENVIRONMENT', 'development')}.yml")
    container.config.from_env("BOURSA", as_=str)
    
    # Configuration requise
    required_configs = [
        "database.url",
        "redis.cache_url", 
        "security.jwt_secret",
    ]
    
    for config_path in required_configs:
        if not container.config.get(config_path):
            raise ValueError(f"Configuration requise manquante: {config_path}")
    
    return container


# ========================================
# 🧪 TESTING STRATEGY
# ========================================

class TestContainer(containers.DeclarativeContainer):
    """Container spécialisé pour les tests"""
    
    # Override avec des mocks
    main_container = providers.DependenciesContainer()
    
    # Database de test en mémoire
    test_database = providers.Resource(
        create_test_database,
        url="sqlite:///:memory:",
    )
    
    # Repositories avec base de test
    test_repositories = providers.Container(
        RepositoryContainer,
        database=providers.Dict({
            'session_factory': providers.Factory(
                create_test_session,
                bind=test_database,
            ),
            'redis_cache': providers.Singleton(FakeRedis),
        })
    )
    
    # Services avec mocks
    mock_yfinance = providers.Singleton(MockYFinanceClient)
    mock_email = providers.Singleton(MockEmailService)


def override_container_for_tests(container: MainContainer) -> None:
    """Override le container principal pour les tests"""
    
    # Override des services externes
    container.infrastructure.yfinance_client.override(MockYFinanceClient())
    container.infrastructure.email_service.override(MockEmailService())
    
    # Override de la base de données
    with container.database.database_engine.override(create_test_database()):
        with container.database.redis_cache.override(FakeRedis()):
            yield container


# ========================================
# 🔄 WIRING AVEC FASTAPI
# ========================================

from dependency_injector.wiring import inject, Provide

@inject
async def create_portfolio_endpoint(
    request_data: CreatePortfolioRequest,
    current_user: User = Depends(get_current_user),
    command: CreatePortfolioCommand = Provide[MainContainer.application.create_portfolio_command],
) -> PortfolioResponse:
    """Endpoint utilisant l'injection de dépendances"""
    portfolio = await command.execute(
        user_id=current_user.id,
        name=request_data.name,
        description=request_data.description,
    )
    return PortfolioResponse.from_domain(portfolio)


# ========================================
# 🚀 APPLICATION STARTUP
# ========================================

def create_app() -> FastAPI:
    """Factory pour créer l'application FastAPI avec DI"""
    
    # Créer et configurer le container
    container = create_main_container()
    
    # Obtenir l'app FastAPI du container
    app = container.web.fastapi_app()
    
    # Attacher le container à l'app pour accès global
    app.container = container
    
    # Wiring automatique des modules
    container.wire(modules=[
        "boursa_vision.infrastructure.web.routers.portfolios",
        "boursa_vision.infrastructure.web.routers.market_data", 
        "boursa_vision.infrastructure.web.routers.auth",
        # ... autres modules
    ])
    
    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ========================================
# 📈 AVANTAGES DE CETTE ARCHITECTURE
# ========================================

"""
✅ MODULARITÉ TOTALE
   - Chaque container a une responsabilité claire
   - Composition flexible selon l'environnement
   - Réutilisabilité maximale

✅ TESTABILITÉ PARFAITE
   - Override facile pour les tests
   - Isolation complète des dépendances
   - Mocks automatiques

✅ PERFORMANCE OPTIMISÉE
   - Lazy loading intelligent
   - Scopes appropriés (Singleton, Factory, Resource)
   - Connection pooling optimisé

✅ CONFIGURATION CENTRALISÉE
   - Source unique de vérité
   - Configuration par environnement
   - Validation automatique

✅ MAINTENANCE SIMPLIFIÉE
   - Architecture explicite et prévisible
   - Séparation claire des responsabilités
   - Évolution facilitée

✅ INTÉGRATION FASTAPI NATIVE
   - Wiring automatique
   - Dependencies type-safe
   - Performance optimale
"""
