# Guide de Test BoursaVision 🧪

> **Version**: 1.0 | **Date**: Décembre 2024  
> **Architecture**: Clean Architecture + CQRS + Dependency Injection  
> **Framework**: pytest 8.4.1 + dependency-injector 4.48.1

## 📋 Table des Matières

- [🎯 Philosophie de Test](#-philosophie-de-test)
- [🏛️ Architecture de Test](#️-architecture-de-test)
- [🔧 Configuration et Outils](#-configuration-et-outils)
- [📚 Types de Tests](#-types-de-tests)
- [🎭 Fixtures et Mocks](#-fixtures-et-mocks)
- [💉 Dependency Injection pour Tests](#-dependency-injection-pour-tests)
- [🏃‍♂️ Stratégies d'Exécution](#️-stratégies-dexécution)
- [📊 Coverage et Métriques](#-coverage-et-métriques)
- [🛠️ Conventions et Standards](#️-conventions-et-standards)
- [🔄 Migration des Tests Existants](#-migration-des-tests-existants)

---

## 🎯 Philosophie de Test

### Principes Fondamentaux

**1. Test-Driven Quality (TDQ)**
- Chaque test doit avoir un **objectif métier clair**
- Pas de tests "pour la forme" - chaque test doit apporter de la valeur
- Focus sur la **behaviour verification** plutôt que l'implémentation

**2. Clean Test Architecture**
- Les tests suivent la même Clean Architecture que l'application
- Séparation claire : Unit → Integration → E2E
- Dependency Injection native pour l'isolation

**3. Fast Feedback Loop**
- Tests unitaires < 100ms par test
- Suite complète < 2 minutes
- Parallélisation intelligente avec pytest-xdist

**4. Reliability First**
- Tests déterministes (pas de flaky tests)
- Isolation complète entre tests
- Gestion explicite des dépendances externes

---

## 🏛️ Architecture de Test

### Structure des Tests

```
tests/
├── conftest.py                 # Configuration globale pytest
├── fixtures/                   # Fixtures réutilisables
│   ├── container_fixtures.py   # DI containers pour tests
│   ├── data_fixtures.py        # Données de test
│   └── mock_fixtures.py        # Mocks et stubs
├── factories/                  # Factory Boy patterns
│   ├── portfolio_factory.py
│   ├── investment_factory.py
│   └── user_factory.py
├── unit/                       # Tests unitaires (< 100ms)
│   ├── domain/                 # Entités et value objects
│   ├── application/            # Use cases et services
│   ├── infrastructure/         # Adapters et repositories
│   └── presentation/           # Controllers et API
├── integration/                # Tests d'intégration
│   ├── database/              # Persistence layer
│   ├── external_apis/         # Services externes
│   └── messaging/             # Event handling
├── e2e/                       # Tests end-to-end
│   ├── api/                   # Tests API complets
│   └── scenarios/             # User scenarios
└── performance/               # Tests de performance
    ├── load/                  # Tests de charge
    └── stress/                # Tests de stress
```

### Mapping avec Clean Architecture

| Couche Architecture | Type Test | Focus | Durée Cible |
|-------------------|-----------|-------|-------------|
| **Domain** | Unit | Logique métier pure | < 50ms |
| **Application** | Unit + Integration | Use cases, CQRS | < 100ms |
| **Infrastructure** | Integration | Repositories, APIs | < 500ms |
| **Presentation** | Integration + E2E | Controllers, validation | < 1s |

---

## 🔧 Configuration et Outils

### Pytest 8.4.1 - Nouvelles Fonctionnalités

**1. Async/Await Native Support**
```python
# Nouveau dans pytest 8.4.1
@pytest.mark.asyncio
async def test_async_use_case(container_fixture):
    # Pas besoin de pytest-asyncio additionnel
    use_case = await container_fixture.application.get_portfolio_use_case()
    result = await use_case.execute(portfolio_id="123")
    assert result.success
```

**2. Improved Fixture Scoping**
```python
# Scoping plus granulaire
@pytest.fixture(scope="session")
def test_container():
    """Container principal pour tous les tests."""
    pass

@pytest.fixture(scope="class") 
def repository_container():
    """Container repository réinitialisé par classe."""
    pass

@pytest.fixture(scope="function")
def clean_database():
    """Base propre pour chaque test."""
    pass
```

**3. Enhanced Parametrize**
```python
# Parametrize avec dependency injection
@pytest.mark.parametrize("use_case", [
    pytest.param("create_portfolio", id="create"),
    pytest.param("update_portfolio", id="update"),
], indirect=True)
def test_portfolio_use_cases(use_case, sample_data):
    result = use_case.execute(sample_data)
    assert result.is_valid()
```

### Configuration pytest.ini Optimisée

```ini
[pytest]
# Chemins et découverte
testpaths = tests
pythonpath = src
python_files = test_*.py *_test.py
python_classes = Test* *Tests
python_functions = test_* should_*

# Exécution asynchrone native
asyncio_mode = auto
asyncio_default_fixture_loop_scope = session

# Performance et parallélisation  
addopts = 
    -v
    --tb=short
    --strict-config
    --maxfail=5
    --no-header
    -x  # Stop à la première erreur en développement
    --lf  # Run last failed d'abord
    --ff  # Failed first
    --durations=10  # Montre les 10 tests les plus lents

# Markers obligatoires
markers =
    unit: Tests unitaires (< 100ms)
    integration: Tests d'intégration (< 1s)
    e2e: Tests end-to-end (< 10s)
    performance: Tests de performance
    slow: Tests lents (> 1s)
    database: Tests nécessitant une base de données
    external: Tests avec services externes
    container: Tests utilisant le DI container

# Filtres d'avertissement
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    error::UserWarning  # Transforme UserWarning en erreur
```

---

## 📚 Types de Tests

### 1. Tests Unitaires (Unit)

**Objectif**: Tester la logique métier en isolation  
**Durée**: < 100ms par test  
**Scope**: Fonction/Méthode individuelle

```python
@pytest.mark.unit
class TestPortfolioDomain:
    """Tests de la logique métier Portfolio."""
    
    def test_portfolio_creation_with_valid_data(self, portfolio_factory):
        """Should create portfolio when data is valid."""
        # Arrange
        data = portfolio_factory.build_data()
        
        # Act
        portfolio = Portfolio.create(data)
        
        # Assert
        assert portfolio.is_valid()
        assert portfolio.name == data["name"]
        assert len(portfolio.investments) == 0
    
    def test_add_investment_increases_total_value(self, portfolio, investment):
        """Should increase portfolio value when investment is added."""
        # Arrange
        initial_value = portfolio.total_value
        
        # Act
        portfolio.add_investment(investment)
        
        # Assert
        assert portfolio.total_value > initial_value
        assert investment in portfolio.investments
```

### 2. Tests d'Intégration (Integration)

**Objectif**: Tester l'interaction entre composants  
**Durée**: < 1s par test  
**Scope**: Interaction entre couches

```python
@pytest.mark.integration
@pytest.mark.database
class TestPortfolioRepository:
    """Tests d'intégration pour PortfolioRepository."""
    
    async def test_save_portfolio_persists_to_database(
        self, 
        test_container,
        clean_database,
        portfolio_factory
    ):
        """Should persist portfolio to database when saved."""
        # Arrange
        repository = test_container.repositories.portfolio_repository()
        portfolio = portfolio_factory.create()
        
        # Act
        saved_portfolio = await repository.save(portfolio)
        
        # Assert
        assert saved_portfolio.id is not None
        
        # Verify persistence
        found_portfolio = await repository.find_by_id(saved_portfolio.id)
        assert found_portfolio == saved_portfolio
```

### 3. Tests End-to-End (E2E)

**Objectif**: Tester les scénarios utilisateur complets  
**Durée**: < 10s par test  
**Scope**: Application complète

```python
@pytest.mark.e2e
@pytest.mark.asyncio
class TestPortfolioManagementScenarios:
    """Tests E2E pour la gestion de portefeuilles."""
    
    async def test_complete_portfolio_lifecycle(
        self,
        test_client,
        authenticated_user_headers
    ):
        """Should handle complete portfolio lifecycle."""
        # Arrange
        portfolio_data = {
            "name": "Tech Portfolio", 
            "description": "Technology investments"
        }
        
        # Act 1: Create Portfolio
        response = await test_client.post(
            "/api/v1/portfolios",
            json=portfolio_data,
            headers=authenticated_user_headers
        )
        assert response.status_code == 201
        portfolio = response.json()
        
        # Act 2: Add Investment
        investment_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        }
        response = await test_client.post(
            f"/api/v1/portfolios/{portfolio['id']}/investments",
            json=investment_data,
            headers=authenticated_user_headers
        )
        assert response.status_code == 201
        
        # Act 3: Retrieve Updated Portfolio
        response = await test_client.get(
            f"/api/v1/portfolios/{portfolio['id']}",
            headers=authenticated_user_headers
        )
        assert response.status_code == 200
        
        # Assert
        updated_portfolio = response.json()
        assert len(updated_portfolio["investments"]) == 1
        assert updated_portfolio["total_value"] > 0
```

---

## 🎭 Fixtures et Mocks

### Fixtures Stratifiées par Couche

```python
# tests/fixtures/container_fixtures.py
"""Fixtures pour l'injection de dépendances."""

import pytest
from boursa_vision.containers.main_clean import MainContainer


@pytest.fixture(scope="session")
def base_test_container():
    """Container de base pour tous les tests."""
    container = MainContainer()
    
    # Override pour l'environnement de test
    container.core.config.override({
        "environment": "testing",
        "database": {"url": "sqlite:///:memory:"},
        "redis": {"url": "redis://localhost:6379/15"},
    })
    
    return container


@pytest.fixture(scope="class")
def test_container(base_test_container):
    """Container avec overrides pour tests d'intégration."""
    container = base_test_container
    
    # Mock des services externes
    container.infrastructure.yfinance_client.override(MockYFinanceClient())
    container.infrastructure.email_service.override(MockEmailService())
    
    yield container
    
    # Cleanup
    container.infrastructure.yfinance_client.reset_override()
    container.infrastructure.email_service.reset_override()


@pytest.fixture
def unit_container(base_test_container):
    """Container pour tests unitaires avec mocks complets."""
    container = base_test_container
    
    # Override tous les repositories avec des mocks
    from unittest.mock import AsyncMock
    
    mock_portfolio_repo = AsyncMock()
    mock_investment_repo = AsyncMock() 
    mock_user_repo = AsyncMock()
    
    container.repositories.portfolio_repository.override(mock_portfolio_repo)
    container.repositories.investment_repository.override(mock_investment_repo)
    container.repositories.user_repository.override(mock_user_repo)
    
    yield container
    
    # Cleanup
    container.repositories.portfolio_repository.reset_override()
    container.repositories.investment_repository.reset_override()
    container.repositories.user_repository.reset_override()
```

### Factory Pattern avec Dependency Injection

```python
# tests/factories/portfolio_factory.py
"""Factory pour les objets Portfolio."""

import factory
from factory import fuzzy
from boursa_vision.domain.entities.portfolio import Portfolio


class PortfolioFactory(factory.Factory):
    """Factory pour créer des objets Portfolio."""
    
    class Meta:
        model = Portfolio
    
    name = factory.Sequence(lambda n: f"Portfolio {n}")
    description = factory.Faker("text", max_nb_chars=200)
    user_id = factory.Faker("uuid4")
    created_at = factory.Faker("date_time_this_year")
    
    @classmethod
    def build_data(cls, **kwargs):
        """Construit uniquement les données sans créer l'objet."""
        return factory.build(dict, FACTORY_FOR=cls._meta.model, **kwargs)
    
    @classmethod
    def create_with_investments(cls, investment_count=3, **kwargs):
        """Crée un portfolio avec des investissements."""
        portfolio = cls.create(**kwargs)
        
        for _ in range(investment_count):
            investment = InvestmentFactory.create()
            portfolio.add_investment(investment)
            
        return portfolio
```

### Mocks Intelligents avec Dependency Injector

```python
# tests/fixtures/mock_fixtures.py
"""Mocks avancés pour les services externes."""

from unittest.mock import AsyncMock, MagicMock
import pytest


class MockYFinanceClient:
    """Mock intelligent du client YFinance."""
    
    def __init__(self):
        self.call_count = 0
        self._market_data = {
            "AAPL": {"price": 150.0, "volume": 1000000},
            "GOOGL": {"price": 2500.0, "volume": 500000},
        }
    
    async def get_stock_price(self, symbol: str) -> float:
        """Mock du prix d'action."""
        self.call_count += 1
        return self._market_data.get(symbol, {"price": 100.0})["price"]
    
    def set_stock_price(self, symbol: str, price: float):
        """Permet de configurer les prix pour les tests."""
        if symbol not in self._market_data:
            self._market_data[symbol] = {"volume": 1000}
        self._market_data[symbol]["price"] = price


@pytest.fixture
def mock_yfinance():
    """Fixture pour le mock YFinance."""
    return MockYFinanceClient()


@pytest.fixture
def spy_email_service():
    """Spy pour vérifier l'envoi d'emails."""
    spy = MagicMock()
    spy.send_email = AsyncMock(return_value=True)
    spy.send_bulk_email = AsyncMock(return_value=True)
    return spy
```

---

## 💉 Dependency Injection pour Tests

### Stratégie d'Override par Couche

```python
# tests/conftest.py
"""Configuration pytest avec DI avancée."""

import pytest
from boursa_vision.containers.main_clean import MainContainer


class TestEnvironmentManager:
    """Gestionnaire d'environnement de test."""
    
    def __init__(self, container: MainContainer):
        self.container = container
        self.overrides = {}
    
    def override_for_unit_tests(self):
        """Configure le container pour les tests unitaires."""
        # Mock tous les I/O
        self.override_database_layer()
        self.override_external_services()
        self.override_infrastructure()
        
    def override_for_integration_tests(self):
        """Configure le container pour les tests d'intégration."""
        # Garde la vraie DB (en mémoire), mock les services externes
        self.override_external_services()
        
    def override_database_layer(self):
        """Override la couche base de données."""
        from unittest.mock import AsyncMock
        
        # Repositories en mode mock
        self.container.repositories.portfolio_repository.override(
            AsyncMock(spec=PortfolioRepository)
        )
        
    def override_external_services(self):
        """Override les services externes."""
        self.container.infrastructure.yfinance_client.override(
            MockYFinanceClient()
        )
        
    def cleanup(self):
        """Nettoie tous les overrides."""
        for override in self.overrides:
            override.reset_override()


@pytest.fixture(scope="session")
def test_environment():
    """Environment de test global."""
    container = MainContainer()
    env_manager = TestEnvironmentManager(container)
    return env_manager


@pytest.fixture
def unit_test_environment(test_environment):
    """Environment pour tests unitaires."""
    test_environment.override_for_unit_tests()
    yield test_environment.container
    test_environment.cleanup()


@pytest.fixture  
def integration_test_environment(test_environment):
    """Environment pour tests d'intégration."""
    test_environment.override_for_integration_tests()
    yield test_environment.container
    test_environment.cleanup()
```

### Fixtures Paramétrées avec DI

```python
@pytest.fixture(params=["memory", "redis", "file"])
def cache_service(request, test_container):
    """Fixture paramétrée pour différents types de cache."""
    cache_type = request.param
    
    if cache_type == "memory":
        service = MemoryCacheService()
    elif cache_type == "redis": 
        service = RedisCacheService(url="redis://localhost:6379/15")
    else:
        service = FileCacheService(path="/tmp/test_cache")
    
    # Override dans le container
    test_container.infrastructure.cache_service.override(service)
    
    yield service
    
    # Cleanup
    test_container.infrastructure.cache_service.reset_override()
    if hasattr(service, 'cleanup'):
        service.cleanup()


@pytest.mark.parametrize("cache_service", ["memory", "redis"], indirect=True)
def test_portfolio_caching_with_different_backends(cache_service, portfolio):
    """Test le cache avec différents backends."""
    # Le test utilise automatiquement le service overridé
    cache_service.set("portfolio_123", portfolio)
    cached = cache_service.get("portfolio_123")
    
    assert cached == portfolio
```

---

## 🏃‍♂️ Stratégies d'Exécution

### Profils d'Exécution par Environnement

```bash
# Développement - Tests rapides seulement
pytest -m "unit and fast" --maxfail=1 -x

# CI/CD - Suite complète
pytest -m "not slow" --cov=src --cov-report=xml --junitxml=results.xml

# Before Push - Tests critiques
pytest -m "unit or (integration and not external)" --durations=10

# Release - Tests complets avec performance
pytest --cov=src --cov-report=html --cov-fail-under=90 -n auto
```

### Configuration par Markers

```python
# pytest.ini markers avancés
markers =
    # Vitesse d'exécution
    fast: Tests < 100ms
    medium: Tests < 1s  
    slow: Tests > 1s
    
    # Types de test
    unit: Tests unitaires
    integration: Tests d'intégration
    e2e: Tests end-to-end
    performance: Tests de performance
    
    # Dépendances
    database: Nécessite une base de données
    redis: Nécessite Redis
    external: Appelle des services externes
    network: Nécessite une connexion réseau
    
    # Domaines métier
    portfolio: Tests liés aux portfolios
    investment: Tests liés aux investissements
    user: Tests liés aux utilisateurs
    auth: Tests d'authentification
    
    # Criticité
    critical: Tests critiques (ne peuvent pas échouer)
    regression: Tests de non-régression
    smoke: Tests de smoke
```

### Parallélisation Intelligente

```python
# conftest.py - Configuration pour pytest-xdist
def pytest_collection_modifyitems(config, items):
    """Optimise la répartition des tests pour la parallélisation."""
    
    # Grouper les tests par type pour éviter les conflits
    for item in items:
        # Tests database dans le même worker
        if "database" in item.keywords:
            item.add_marker(pytest.mark.xdist_group(name="database"))
            
        # Tests externes séparés
        if "external" in item.keywords:
            item.add_marker(pytest.mark.xdist_group(name="external"))
            
        # Tests unitaires répartis librement
        if "unit" in item.keywords:
            item.add_marker(pytest.mark.xdist_group(name=f"unit_{hash(item.nodeid) % 4}"))
```

---

## 📊 Coverage et Métriques

### Configuration Coverage Avancée

```ini
# .coveragerc
[run]
source = src/
omit = 
    */tests/*
    */migrations/*
    */conftest.py
    */factories.py
    */__pycache__/*

[report]
# Seuils de coverage par type
fail_under = 85
show_missing = true
skip_covered = false

# Exclude des lignes spécifiques
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
title = BoursaVision Test Coverage

[xml]
output = coverage.xml
```

### Métriques par Couche d'Architecture

```python
# tests/test_coverage_requirements.py
"""Tests pour vérifier les exigences de coverage par couche."""

import pytest
import coverage
from pathlib import Path


class TestCoverageRequirements:
    """Vérifie que chaque couche respecte ses exigences de coverage."""
    
    def test_domain_layer_coverage_above_95_percent(self):
        """Domain layer doit avoir > 95% de coverage."""
        cov = coverage.Coverage()
        cov.load()
        
        domain_files = Path("src/boursa_vision/domain").rglob("*.py") 
        total_lines = 0
        covered_lines = 0
        
        for file in domain_files:
            analysis = cov.analysis2(str(file))
            total_lines += len(analysis[1]) + len(analysis[2]) 
            covered_lines += len(analysis[1])
            
        coverage_percent = (covered_lines / total_lines) * 100
        assert coverage_percent > 95, f"Domain coverage: {coverage_percent:.1f}%"
    
    def test_application_layer_coverage_above_90_percent(self):
        """Application layer doit avoir > 90% de coverage."""
        # Implémentation similaire pour application/
        pass
    
    def test_infrastructure_layer_coverage_above_80_percent(self):
        """Infrastructure layer doit avoir > 80% de coverage."""
        # Implémentation similaire pour infrastructure/
        pass
```

### Reporting et Dashboards

```python
# scripts/generate_test_report.py
"""Génère un rapport de test complet."""

import json
from pathlib import Path
import pytest
import coverage
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TestMetrics:
    """Métriques de test par couche."""
    layer: str
    test_count: int
    coverage_percent: float
    avg_test_duration: float
    failed_tests: List[str]


def generate_comprehensive_report():
    """Génère un rapport de test complet."""
    
    # Exécuter les tests avec métriques
    pytest_args = [
        "--json-report", 
        "--json-report-file=test_results.json",
        "--durations=0",
        "--cov=src",
        "--cov-report=json"
    ]
    
    pytest.main(pytest_args)
    
    # Analyser les résultats
    with open("test_results.json") as f:
        test_results = json.load(f)
        
    with open("coverage.json") as f:
        coverage_results = json.load(f)
    
    # Générer le rapport par couche
    layers = ["domain", "application", "infrastructure", "presentation"]
    metrics = []
    
    for layer in layers:
        layer_metrics = analyze_layer_metrics(layer, test_results, coverage_results)
        metrics.append(layer_metrics)
    
    # Générer rapport HTML
    generate_html_report(metrics)
    
    # Générer dashboard JSON pour intégration CI/CD
    generate_dashboard_data(metrics)


def analyze_layer_metrics(layer: str, test_results: dict, coverage_results: dict) -> TestMetrics:
    """Analyse les métriques pour une couche spécifique."""
    
    # Filter tests by layer
    layer_tests = [
        test for test in test_results["tests"] 
        if f"/{layer}/" in test["nodeid"]
    ]
    
    # Calculate metrics
    test_count = len(layer_tests)
    failed_tests = [test["nodeid"] for test in layer_tests if test["outcome"] == "failed"]
    
    if test_count > 0:
        avg_duration = sum(test["duration"] for test in layer_tests) / test_count
    else:
        avg_duration = 0
    
    # Calculate coverage for layer
    layer_files = [
        file for file in coverage_results["files"] 
        if f"/{layer}/" in file
    ]
    
    if layer_files:
        total_coverage = sum(
            coverage_results["files"][file]["summary"]["percent_covered"] 
            for file in layer_files
        ) / len(layer_files)
    else:
        total_coverage = 0
    
    return TestMetrics(
        layer=layer,
        test_count=test_count,
        coverage_percent=total_coverage,
        avg_test_duration=avg_duration,
        failed_tests=failed_tests
    )
```

---

## 🛠️ Conventions et Standards

### Nomenclature des Tests

```python
# Convention de nommage descriptive
class TestPortfolioCreation:
    """Tests pour la création de portefeuilles."""
    
    def test_should_create_portfolio_when_data_is_valid(self):
        """Should create portfolio when all required data is provided and valid."""
        pass
    
    def test_should_raise_validation_error_when_name_is_empty(self):
        """Should raise ValidationError when portfolio name is empty or None."""
        pass
    
    def test_should_assign_unique_id_when_portfolio_is_created(self):
        """Should assign a unique UUID when a new portfolio is successfully created."""
        pass


# Convention pour les tests paramétrés
class TestPortfolioValidation:
    """Tests de validation pour les portefeuilles."""
    
    @pytest.mark.parametrize("invalid_name", [
        pytest.param("", id="empty_string"),
        pytest.param(None, id="none_value"), 
        pytest.param("   ", id="whitespace_only"),
        pytest.param("a" * 256, id="too_long"),
    ])
    def test_should_reject_invalid_portfolio_names(self, invalid_name):
        """Should reject portfolio creation when name is invalid."""
        pass
```

### Structure AAA (Arrange-Act-Assert)

```python
def test_portfolio_value_calculation_with_multiple_investments(
    self, 
    portfolio_factory,
    investment_factory
):
    """Should calculate correct total value when portfolio contains multiple investments."""
    
    # Arrange - Configuration du test
    portfolio = portfolio_factory.create(name="Tech Portfolio")
    
    apple_investment = investment_factory.create(
        symbol="AAPL", 
        quantity=10, 
        price=150.0
    )
    google_investment = investment_factory.create(
        symbol="GOOGL",
        quantity=5,
        price=2500.0
    )
    
    expected_total = (10 * 150.0) + (5 * 2500.0)
    
    # Act - Exécution de l'action testée
    portfolio.add_investment(apple_investment)
    portfolio.add_investment(google_investment)
    
    actual_total = portfolio.calculate_total_value()
    
    # Assert - Vérification des résultats
    assert actual_total == expected_total
    assert len(portfolio.investments) == 2
    assert apple_investment in portfolio.investments
    assert google_investment in portfolio.investments
```

### Gestion des Erreurs et Edge Cases

```python
class TestPortfolioEdgeCases:
    """Tests des cas limites pour les portefeuilles."""
    
    def test_should_handle_empty_portfolio_gracefully(self, empty_portfolio):
        """Should handle operations on empty portfolio without errors."""
        # Test des opérations sur portfolio vide
        assert empty_portfolio.total_value == 0
        assert len(empty_portfolio.investments) == 0
        assert empty_portfolio.is_diversified() is False
    
    def test_should_handle_negative_investment_values(self, portfolio):
        """Should handle negative investment values correctly."""
        # Cas où un investissement perd de la valeur
        negative_investment = Investment(
            symbol="LOSS", 
            quantity=10, 
            purchase_price=100.0,
            current_price=50.0  # Perte de 50%
        )
        
        portfolio.add_investment(negative_investment)
        
        # Vérifier que la perte est correctement calculée
        assert portfolio.total_unrealized_gain < 0
        assert portfolio.total_value == 500.0  # 10 * 50
    
    @pytest.mark.parametrize("extreme_value", [
        pytest.param(float('inf'), id="infinite_value"),
        pytest.param(float('-inf'), id="negative_infinite"),
        pytest.param(float('nan'), id="not_a_number"),
        pytest.param(1e308, id="very_large_number"),
    ])
    def test_should_handle_extreme_numeric_values(self, extreme_value, portfolio):
        """Should handle extreme numeric values gracefully."""
        with pytest.raises(ValueError, match="Invalid numeric value"):
            investment = Investment(symbol="EXTREME", quantity=1, price=extreme_value)
            portfolio.add_investment(investment)
```

---

## 🔄 Migration des Tests Existants

### Plan de Migration en Phases

**Phase 1: Audit et Inventaire (Semaine 1)**
```python
# Script d'audit des tests existants
def audit_existing_tests():
    """Audit des tests existants pour planifier la migration."""
    
    test_files = Path("tests").rglob("test_*.py")
    audit_report = {
        "total_tests": 0,
        "by_category": {"unit": 0, "integration": 0, "e2e": 0, "unknown": 0},
        "by_status": {"passing": 0, "failing": 0, "ignored": 0},
        "migration_candidates": [],
        "deletion_candidates": []
    }
    
    for test_file in test_files:
        # Analyser chaque fichier de test
        tests_in_file = analyze_test_file(test_file)
        
        for test in tests_in_file:
            audit_report["total_tests"] += 1
            
            # Catégoriser le test
            category = categorize_test(test)
            audit_report["by_category"][category] += 1
            
            # Évaluer la qualité
            if is_migration_candidate(test):
                audit_report["migration_candidates"].append(test)
            elif should_be_deleted(test):
                audit_report["deletion_candidates"].append(test)
    
    generate_audit_report(audit_report)
    return audit_report
```

**Phase 2: Migration par Couches (Semaines 2-4)**

```python
# Exemples de migration de tests existants

# AVANT: Test ancien sans DI
def test_portfolio_creation_old():
    """Test ancien avec dépendances hardcodées."""
    
    # Problèmes: hardcoded DB, pas d'isolation, lent
    db = PostgresDatabase(url="postgresql://...")
    repo = PortfolioRepository(db)
    
    portfolio_data = {"name": "Test Portfolio"}
    portfolio = repo.create(portfolio_data)
    
    assert portfolio.name == "Test Portfolio"


# APRÈS: Test modernisé avec DI  
@pytest.mark.unit
def test_portfolio_creation_new(unit_container, portfolio_factory):
    """Should create portfolio when valid data is provided."""
    
    # Arrange - DI container avec mocks
    use_case = unit_container.application.create_portfolio_use_case()
    portfolio_data = portfolio_factory.build_data()
    
    # Act
    result = use_case.execute(portfolio_data)
    
    # Assert
    assert result.success
    assert result.portfolio.name == portfolio_data["name"]
```

**Phase 3: Optimisation et Standardisation (Semaine 5)**

```python
# Refactoring des fixtures communes
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuration automatique de l'environnement de test."""
    
    # Configuration des logs en mode test
    import logging
    logging.getLogger("boursa_vision").setLevel(logging.WARNING)
    
    # Désactiver les connexions externes
    import os
    os.environ["YFINANCE_MOCK_MODE"] = "true"
    os.environ["REDIS_MOCK_MODE"] = "true"
    
    yield
    
    # Cleanup global
    cleanup_test_artifacts()


def cleanup_test_artifacts():
    """Nettoie les artefacts de test."""
    
    # Supprimer les fichiers temporaires
    import tempfile
    import shutil
    
    temp_dirs = ["/tmp/boursa_test_*", "/tmp/pytest-*"]
    for pattern in temp_dirs:
        for path in glob.glob(pattern):
            shutil.rmtree(path, ignore_errors=True)
```

### Checklist de Migration

- [ ] **Audit Initial**
  - [ ] Inventaire des tests existants 
  - [ ] Identification des tests obsolètes
  - [ ] Analyse des dépendances hardcodées

- [ ] **Configuration**
  - [ ] Mise à jour pytest.ini
  - [ ] Configuration des markers
  - [ ] Setup des fixtures DI

- [ ] **Migration des Tests**
  - [ ] Tests Domain (priorité haute)
  - [ ] Tests Application (priorité haute) 
  - [ ] Tests Infrastructure (priorité moyenne)
  - [ ] Tests Presentation (priorité basse)

- [ ] **Validation**
  - [ ] Coverage par couche respecté
  - [ ] Performance des tests < seuils
  - [ ] Stabilité (pas de flaky tests)

- [ ] **Documentation**
  - [ ] Guide des fixtures
  - [ ] Exemples par type de test
  - [ ] Conventions d'équipe

---

## 📈 Métriques et KPIs de Réussite

### Objectifs Quantitatifs

| Métrique | Objectif | Actuel | Status |
|----------|----------|---------|--------|
| **Test Coverage** | > 85% | 73% | 🔄 En cours |
| **Domain Coverage** | > 95% | - | ⏳ À mesurer |
| **Test Speed** | < 2min suite complète | ~5min | 🔄 En cours |  
| **Unit Test Speed** | < 100ms par test | - | ⏳ À mesurer |
| **Flaky Tests** | 0% | - | ⏳ À mesurer |
| **Test Maintenance** | < 10% effort dev | - | ⏳ À mesurer |

### Monitoring et Alertes

```python
# tests/monitoring/test_health_metrics.py
"""Tests de monitoring de la santé de la suite de test."""

import time
import pytest
from pathlib import Path


class TestSuiteHealthMetrics:
    """Métriques de santé de la suite de test."""
    
    def test_unit_tests_execution_time_under_threshold(self):
        """Les tests unitaires doivent s'exécuter en moins de 100ms chacun."""
        
        start_time = time.time()
        
        # Exécuter tous les tests unitaires
        result = pytest.main(["-m", "unit", "--tb=no", "-q"])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Compter le nombre de tests unitaires
        unit_test_count = count_tests_with_marker("unit")
        
        if unit_test_count > 0:
            avg_time_per_test = (execution_time / unit_test_count) * 1000  # en ms
            assert avg_time_per_test < 100, f"Tests unitaires trop lents: {avg_time_per_test:.1f}ms en moyenne"
    
    def test_no_ignored_tests_in_production_code(self):
        """Aucun test ne doit être ignoré dans le code de production."""
        
        test_files = Path("tests").rglob("*.py")
        ignored_tests = []
        
        for test_file in test_files:
            content = test_file.read_text()
            
            # Chercher les patterns d'ignore
            ignore_patterns = ["@pytest.mark.skip", "pytest.skip(", "# TODO: fix"]
            
            for pattern in ignore_patterns:
                if pattern in content:
                    ignored_tests.append(str(test_file))
                    
        assert len(ignored_tests) == 0, f"Tests ignorés trouvés: {ignored_tests}"
    
    def test_test_coverage_regression_protection(self):
        """Protection contre la régression du coverage."""
        
        import coverage
        cov = coverage.Coverage()
        cov.load()
        
        current_coverage = cov.report(show_missing=False)
        minimum_coverage = 85.0  # Seuil minimum
        
        assert current_coverage >= minimum_coverage, \
            f"Coverage en régression: {current_coverage:.1f}% < {minimum_coverage}%"
```

---

## 🎯 Conclusion

Ce guide établit les fondations d'une architecture de test moderne, robuste et maintenable pour BoursaVision. Les principes énoncés garantissent :

- **🚀 Performance**: Tests rapides avec feedback immédiat
- **🔒 Fiabilité**: Tests déterministes et isolés  
- **🧠 Intelligibilité**: Tests expressifs et documentés
- **🔧 Maintenabilité**: Architecture évolutive avec le produit
- **⚡ Productivity**: Outils et conventions qui accélèrent le développement

**Prochaines étapes:**
1. ✅ Appliquer les conventions aux nouveaux tests
2. 🔄 Migrer progressivement les tests existants  
3. 📊 Mettre en place le monitoring des métriques
4. 🎓 Former l'équipe aux nouveaux standards

---

*Guide maintenu par l'équipe BoursaVision • Dernière mise à jour: Décembre 2024*
