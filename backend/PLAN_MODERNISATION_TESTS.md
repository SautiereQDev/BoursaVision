# Plan de Modernisation des Tests - BoursaVision 🔄

> **Objectif**: Mettre à jour l'architecture de tests pour correspondre à la nouvelle architecture avec dependency injection et profiter de pytest 8.4.1

## 📋 Analyse de l'État Actuel

### Points Faibles Identifiés

1. **Configuration pytest.ini trop restrictive**
   - Beaucoup de fichiers ignorés (20+ ignores)
   - Pas d'utilisation des nouveautés pytest 8.4.1
   - Markers définis mais pas exploités

2. **Fixtures conftest.py basique**
   - Pas d'intégration avec dependency injection
   - Mocks manuels au lieu d'utiliser le container DI
   - Scope des fixtures non optimisé

3. **Tests sans logique métier claire**
   - Tests d'infrastructure mélangés aux tests unitaires
   - Pas de séparation Domain/Application/Infrastructure
   - Coverage artificiellement gonflé

4. **Dépendances hardcodées**
   - Connexions directes aux services externes
   - Pas d'isolation entre tests
   - Tests lents (> 5 minutes pour la suite)

## 🎯 Actions Concrètes à Entreprendre

### 1. Refactoring Configuration (Priorité: HAUTE)

#### Nouveau pytest.ini
```ini
[pytest]
# Configuration moderne avec pytest 8.4.1
testpaths = tests
pythonpath = src
python_files = test_*.py *_test.py
python_classes = Test* *Tests  
python_functions = test_* should_*

# Asyncio natif avec pytest 8.4.1
asyncio_mode = auto
asyncio_default_fixture_loop_scope = session

# Performance et développement
addopts = 
    -v
    --tb=short
    --strict-config
    --maxfail=1  # Stop au premier échec en dev
    --lf  # Last failed first
    --ff  # Failed first
    --durations=10
    --disable-warnings  # Réduire le bruit

# Markers pour architecture propre
markers =
    # Performance
    fast: Tests < 100ms
    slow: Tests > 1s
    
    # Architecture layers  
    domain: Tests de la couche domain
    application: Tests de la couche application
    infrastructure: Tests de la couche infrastructure
    presentation: Tests de la couche presentation
    
    # Types de test
    unit: Tests unitaires avec mocks complets
    integration: Tests d'intégration avec vrais composants
    e2e: Tests end-to-end avec API complète
    
    # Dépendances
    database: Nécessite une base de données
    external: Appelle des services externes
    container: Utilise le container DI

# Plus d'ignores - utiliser les markers à la place
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### 2. Nouveau conftest.py avec DI (Priorité: HAUTE)

```python
"""Configuration pytest moderne avec Dependency Injection."""

import pytest
import asyncio
from pathlib import Path
import sys

# Import du container principal
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from boursa_vision.containers.main_clean import MainContainer
from unittest.mock import AsyncMock, MagicMock


# =====================================
# CONTAINER FIXTURES (Session Scope)
# =====================================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop pour toute la session de test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def base_container():
    """Container de base pour tous les tests."""
    container = MainContainer()
    
    # Configuration test globale
    container.core.config.override({
        "environment": "testing",
        "database": {
            "url": "sqlite+aiosqlite:///:memory:",
            "echo": False
        },
        "redis": {
            "url": "redis://localhost:6379/15"
        }
    })
    
    return container


@pytest.fixture(scope="session")  
def test_container(base_container):
    """Container avec overrides pour environnement de test."""
    container = base_container
    
    # Mock des services externes au niveau session
    from tests.mocks.external_services import (
        MockYFinanceClient, 
        MockEmailService,
        MockCeleryApp
    )
    
    container.infrastructure.yfinance_client.override(MockYFinanceClient())
    container.infrastructure.email_service.override(MockEmailService())
    container.infrastructure.celery_app.override(MockCeleryApp())
    
    yield container
    
    # Cleanup session
    container.infrastructure.yfinance_client.reset_override()
    container.infrastructure.email_service.reset_override()
    container.infrastructure.celery_app.reset_override()


# =====================================
# FIXTURES PAR TYPE DE TEST
# =====================================

@pytest.fixture
def unit_container(test_container):
    """Container pour tests unitaires avec mocks complets."""
    container = test_container
    
    # Mock tous les repositories
    mock_portfolio_repo = AsyncMock()
    mock_investment_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    
    container.repositories.portfolio_repository.override(mock_portfolio_repo)
    container.repositories.investment_repository.override(mock_investment_repo) 
    container.repositories.user_repository.override(mock_user_repo)
    
    # Mock les services domain
    mock_portfolio_service = MagicMock()
    mock_scoring_service = MagicMock()
    
    container.services.portfolio_service.override(mock_portfolio_service)
    container.services.scoring_service.override(mock_scoring_service)
    
    yield container
    
    # Cleanup
    container.repositories.portfolio_repository.reset_override()
    container.repositories.investment_repository.reset_override()
    container.repositories.user_repository.reset_override()
    container.services.portfolio_service.reset_override()
    container.services.scoring_service.reset_override()


@pytest.fixture
def integration_container(test_container):
    """Container pour tests d'intégration."""
    # Garde les vraies implémentations repositories
    # Mais mock les services externes
    yield test_container


@pytest.fixture
async def e2e_container(test_container):
    """Container pour tests E2E avec FastAPI."""
    # Application complète avec tous les routers
    app = test_container.app()
    
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client, test_container


# =====================================
# DATA FACTORIES
# =====================================

@pytest.fixture
def portfolio_data():
    """Données de portefeuille valides pour les tests."""
    return {
        "name": "Tech Portfolio",
        "description": "Technology investments",
        "user_id": "test-user-123"
    }


@pytest.fixture  
def investment_data():
    """Données d'investissement valides pour les tests."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "quantity": 10,
        "purchase_price": 150.0,
        "current_price": 160.0
    }


@pytest.fixture
def user_data():
    """Données utilisateur valides pour les tests."""
    return {
        "id": "test-user-123",
        "email": "test@example.com", 
        "first_name": "Test",
        "last_name": "User"
    }


# =====================================
# UTILITIES
# =====================================

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset automatique des mocks entre chaque test."""
    yield
    # Cleanup automatique si nécessaire
    

def pytest_configure(config):
    """Configuration pytest au démarrage."""
    # Ajouter des markers dynamiques si nécessaire
    config.addinivalue_line("markers", "wip: Work in progress tests")


def pytest_collection_modifyitems(config, items):
    """Modifier la collection de tests pour optimisation."""
    # Trier les tests rapides en premier
    items.sort(key=lambda x: "fast" not in x.keywords)
```

### 3. Structure de Tests Réorganisée (Priorité: MOYENNE)

#### Nouveau découpage par couche architecturale

```
tests/
├── conftest.py                    # Configuration DI globale
├── mocks/                         # Mocks réutilisables
│   ├── external_services.py       # YFinance, Email, etc.
│   └── repositories.py            # Repository mocks
├── fixtures/                      # Fixtures par domaine
│   ├── container_fixtures.py      # DI containers
│   ├── portfolio_fixtures.py      # Portfolio factories
│   └── market_data_fixtures.py    # Market data samples
├── unit/                          # Tests unitaires purs
│   ├── domain/                    # Entités & Value Objects
│   │   ├── test_portfolio_entity.py
│   │   └── test_investment_value_object.py
│   ├── application/               # Use Cases & Services
│   │   ├── commands/
│   │   │   ├── test_create_portfolio_command.py
│   │   │   └── test_add_investment_command.py
│   │   └── queries/
│   │       └── test_portfolio_query_handler.py
│   └── infrastructure/            # Adapters (avec mocks)
│       ├── test_portfolio_repository.py
│       └── test_yfinance_adapter.py
├── integration/                   # Tests d'intégration
│   ├── database/                  # Vraie DB (en mémoire)
│   │   └── test_portfolio_persistence.py
│   ├── api/                       # Tests API layer
│   │   └── test_portfolio_endpoints.py
│   └── services/                  # Services avec vraies implémentations
│       └── test_portfolio_service_integration.py
├── e2e/                           # Tests end-to-end
│   ├── scenarios/                 # User scenarios complets
│   │   └── test_portfolio_management_scenario.py
│   └── api/                       # API tests complets
│       └── test_full_portfolio_workflow.py
└── performance/                   # Tests de performance
    └── test_portfolio_load.py
```

### 4. Exemples de Migration par Type

#### A. Migration Test Unitaire Domain

**AVANT (test existant problématique)**:
```python
def test_portfolio_creation():
    """Test basique sans logique claire."""
    portfolio = Portfolio("Test")
    assert portfolio.name == "Test"
```

**APRÈS (test moderne avec DI)**:
```python
@pytest.mark.unit
@pytest.mark.domain
def test_should_create_valid_portfolio_when_data_is_correct(portfolio_data):
    """Should create a valid portfolio when all required data is provided."""
    # Arrange
    expected_name = portfolio_data["name"]
    expected_description = portfolio_data["description"]
    
    # Act
    portfolio = Portfolio.create(portfolio_data)
    
    # Assert
    assert portfolio.is_valid()
    assert portfolio.name == expected_name
    assert portfolio.description == expected_description
    assert portfolio.total_value == 0.0
    assert len(portfolio.investments) == 0
```

#### B. Migration Test Application avec DI

**AVANT (dépendances hardcodées)**:
```python
def test_create_portfolio_use_case():
    """Test avec dépendances hardcodées."""
    db = TestDatabase() 
    repo = PortfolioRepository(db)
    use_case = CreatePortfolioUseCase(repo)
    
    result = use_case.execute({"name": "Test"})
    assert result is not None
```

**APRÈS (avec container DI)**:
```python
@pytest.mark.unit  
@pytest.mark.application
async def test_create_portfolio_command_should_create_and_return_portfolio(
    unit_container,
    portfolio_data
):
    """Should create portfolio through command handler when data is valid."""
    # Arrange
    command_handler = unit_container.application.create_portfolio_command()
    
    # Configure mock repository response
    expected_portfolio = Portfolio.create(portfolio_data)
    mock_repo = unit_container.repositories.portfolio_repository()
    mock_repo.save.return_value = expected_portfolio
    
    # Act
    result = await command_handler.execute(
        name=portfolio_data["name"],
        description=portfolio_data["description"],
        user_id=portfolio_data["user_id"]
    )
    
    # Assert
    assert result.success
    assert result.portfolio.name == portfolio_data["name"]
    mock_repo.save.assert_called_once()
```

#### C. Migration Test E2E avec FastAPI

**APRÈS (E2E moderne avec DI)**:
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_portfolio_creation_workflow(
    e2e_container,
    portfolio_data,
    investment_data
):
    """Should handle complete portfolio creation and investment workflow."""
    client, container = e2e_container
    
    # Act 1: Create Portfolio
    response = await client.post("/api/v1/portfolios", json=portfolio_data)
    assert response.status_code == 201
    
    created_portfolio = response.json()
    portfolio_id = created_portfolio["id"]
    
    # Act 2: Add Investment  
    investment_payload = {**investment_data, "portfolio_id": portfolio_id}
    response = await client.post(
        f"/api/v1/portfolios/{portfolio_id}/investments",
        json=investment_payload
    )
    assert response.status_code == 201
    
    # Act 3: Retrieve Updated Portfolio
    response = await client.get(f"/api/v1/portfolios/{portfolio_id}")
    assert response.status_code == 200
    
    # Assert Final State
    final_portfolio = response.json()
    assert len(final_portfolio["investments"]) == 1
    assert final_portfolio["total_value"] > 0
```

### 5. Commandes de Migration

#### Étape 1: Backup et préparation
```bash
# Sauvegarder les tests actuels
git checkout -b backup-old-tests
git add tests/ && git commit -m "Backup: existing tests before migration"

# Créer branche de migration
git checkout develop
git checkout -b modernize-tests
```

#### Étape 2: Appliquer la nouvelle configuration
```bash
# Remplacer pytest.ini
cp pytest.ini pytest.ini.old
# [Appliquer la nouvelle configuration]

# Remplacer conftest.py
cp tests/conftest.py tests/conftest.py.old
# [Appliquer le nouveau conftest.py avec DI]
```

#### Étape 3: Créer les mocks et fixtures
```bash
mkdir -p tests/mocks tests/fixtures
# [Créer les nouveaux fichiers de mocks avec DI]
```

#### Étape 4: Migration progressive par couche
```bash
# Tests Domain d'abord (plus simples)
mkdir -p tests/unit/domain
# [Migrer tests domain]

# Tests Application ensuite  
mkdir -p tests/unit/application/{commands,queries}
# [Migrer tests application]

# Tests Infrastructure et E2E en dernier
mkdir -p tests/{integration,e2e}/{database,api,scenarios}
# [Migrer tests integration/e2e]
```

#### Étape 5: Validation et nettoyage
```bash
# Tester la nouvelle suite
poetry run pytest -m "fast and unit" --maxfail=5

# Coverage par couche
poetry run pytest --cov=src/boursa_vision/domain tests/unit/domain/
poetry run pytest --cov=src/boursa_vision/application tests/unit/application/

# Supprimer les anciens tests devenus obsolètes
# [Après validation que les nouveaux tests couvrent tout]
```

## 📊 Critères de Succès

### Métriques Before/After

| Métrique | Avant | Objectif Après |
|----------|-------|----------------|
| **Temps suite complète** | ~5 min | < 2 min |
| **Temps tests unitaires** | ~2 min | < 30s |
| **Coverage Domain** | ? | > 95% |
| **Coverage Application** | ? | > 90% |
| **Nombre de tests ignored** | 20+ | 0 |
| **Tests flaky** | ? | 0 |

### Validation Quality Gates

- [ ] ✅ Tous les tests passent sans warnings
- [ ] ✅ Aucun test ignoré (skip/ignore) 
- [ ] ✅ Coverage par couche respecté
- [ ] ✅ Performance < seuils définis
- [ ] ✅ Documentation à jour
- [ ] ✅ Équipe formée aux nouveaux standards

## 🚀 Planning de Migration

**Semaine 1**: Configuration et infrastructure
- Nouveau pytest.ini et conftest.py  
- Mocks et fixtures avec DI
- Tests de validation infrastructure

**Semaine 2**: Migration couche Domain  
- Tests entités et value objects
- Tests services domain purs
- Validation coverage Domain > 95%

**Semaine 3**: Migration couche Application
- Tests commandes et queries CQRS
- Tests use cases avec DI
- Validation coverage Application > 90%

**Semaine 4**: Migration Infrastructure et E2E
- Tests repositories avec vraie DB
- Tests API endpoints
- Tests scénarios utilisateur complets

**Semaine 5**: Optimisation et documentation
- Tuning performance  
- Documentation finale
- Formation équipe

---

*Plan de migration créé le: Décembre 2024*
*Statut: 📋 Prêt pour exécution*
