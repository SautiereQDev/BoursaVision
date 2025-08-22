# Architecture de Tests - BoursaVision Backend

## Philosophie de Tests

### Principes Fondamentaux

1. **Test Pyramid** : Privilégier les tests unitaires rapides, complémentés par des tests d'intégration et E2E ciblés
2. **Clean Architecture Testing** : Tests alignés avec l'architecture (Domain → Application → Infrastructure)
3. **Test Isolation** : Chaque test doit être indépendant et reproductible
4. **Coverage Progressif** : 25% → 50% → 75% → 90% avec focus sur le code critique
5. **Performance** : Tests rapides (<100ms unitaires, <1s intégration)

### Types de Tests

#### 🔥 Tests Unitaires (`@pytest.mark.unit`)
- **Scope** : Classes isolées, méthodes individuelles
- **Vitesse** : < 100ms par test
- **Mocking** : Toutes les dépendances externes
- **Coverage** : Domain entities, Value Objects, Application services

#### 🔗 Tests d'Intégration (`@pytest.mark.integration`)
- **Scope** : Interaction entre composants
- **Vitesse** : < 1s par test
- **Dependencies** : Base de données de test, services externes mockés
- **Coverage** : Repositories, Mappers, Use Cases avec vraies DB

#### 📋 Tests de Contrat (`@pytest.mark.contract`)
- **Scope** : Interfaces API, schémas DB
- **Purpose** : Vérifier les contrats entre couches
- **Coverage** : DTOs, API responses, Database schemas

#### 🌐 Tests End-to-End (`@pytest.mark.e2e`)
- **Scope** : Workflows métier complets
- **Vitesse** : < 5s par test
- **Environment** : Environnement le plus proche de production
- **Coverage** : User journeys critiques

## Structure des Tests

```
tests/
├── conftest.py                 # Configuration globale pytest
├── fixtures/                   # Fixtures communes réutilisables
│   ├── auth_fixtures.py
│   ├── database_fixtures.py
│   └── market_data_fixtures.py
├── factories/                  # Factory classes avec Faker
│   ├── investment_factory.py
│   ├── portfolio_factory.py
│   ├── user_factory.py
│   └── market_data_factory.py
├── unit/                       # Tests unitaires rapides
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── test_investment.py
│   │   │   ├── test_portfolio.py
│   │   │   └── test_position.py
│   │   ├── value_objects/
│   │   │   ├── test_money.py
│   │   │   ├── test_price.py
│   │   │   └── test_signal.py
│   │   └── services/
│   │       └── test_portfolio_allocation_service.py
│   └── application/
│       ├── mappers/
│       │   ├── test_investment_mapper.py
│       │   └── test_portfolio_mapper.py
│       ├── use_cases/
│       │   ├── test_find_investments.py
│       │   └── test_analyze_portfolio.py
│       └── services/
├── integration/                # Tests d'intégration
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── test_investment_repository.py
│   │   │   ├── test_portfolio_repository.py
│   │   │   └── test_mappers_integration.py
│   │   └── external/
│   │       └── test_yfinance_service.py
│   └── application/
│       └── test_use_cases_integration.py
└── e2e/                       # Tests end-to-end
    ├── test_investment_workflow.py
    ├── test_portfolio_management.py
    └── test_user_journey.py
```

## Conventions de Code

### Nommage des Tests

```python
# Unitaires
def test_should_create_investment_when_valid_data_provided():
def test_should_raise_exception_when_negative_price():
def test_should_calculate_portfolio_value_correctly():

# Intégration  
def test_investment_repository_should_persist_and_retrieve():
def test_portfolio_mapper_should_convert_domain_to_persistence():

# E2E
def test_user_can_create_portfolio_and_add_investments():
```

### Structure d'un Test (AAA Pattern)

```python
def test_should_calculate_unrealized_pnl():
    # Arrange - Setup test data
    position = create_position(
        symbol="AAPL",
        quantity=100,
        average_price=Money(Decimal("150.00"), Currency.USD)
    )
    current_price = Money(Decimal("160.00"), Currency.USD)
    
    # Act - Execute the method under test
    pnl = position.calculate_unrealized_pnl(current_price)
    
    # Assert - Verify the results
    expected_pnl = Money(Decimal("1000.00"), Currency.USD)
    assert pnl == expected_pnl
```

### Fixtures et Factories

#### Fixtures pour Configuration
```python
@pytest.fixture(scope="session")
async def test_database():
    """Database de test pour les tests d'intégration."""
    
@pytest.fixture
def mock_investment_repository():
    """Mock repository pour tests unitaires."""
```

#### Factories pour Données de Test
```python
class InvestmentFactory(factory.Factory):
    class Meta:
        model = Investment
    
    symbol = factory.Faker('stock_symbol')
    name = factory.Faker('company')
    sector = factory.Faker('random_element', elements=list(InvestmentSector))
```

## Markers et Exécution

### Markers Organisés

```python
# Types principaux
@pytest.mark.unit           # Tests unitaires rapides
@pytest.mark.integration    # Tests d'intégration  
@pytest.mark.e2e           # Tests end-to-end
@pytest.mark.contract      # Tests de contrat

# Performance
@pytest.mark.fast          # < 100ms
@pytest.mark.slow          # > 1s

# Dépendances
@pytest.mark.database      # Nécessite DB
@pytest.mark.external      # Services externes
@pytest.mark.network       # Accès réseau

# Domaines
@pytest.mark.portfolio     # Tests portfolio
@pytest.mark.investment    # Tests investment
@pytest.mark.auth          # Tests authentification
```

### Commandes d'Exécution

```bash
# Tous les tests unitaires (rapides)
pytest -m unit

# Tests d'intégration avec DB
pytest -m "integration and database"

# Tests lents en parallèle
pytest -m slow -n auto

# Tests avec coverage
pytest --cov=src/boursa_vision --cov-report=html

# Tests par domaine
pytest -m portfolio
pytest -m investment

# Tests de régression
pytest -m "not wip"
```

## Métriques de Qualité

### Coverage Targets (Progressif)

| Composant | Phase 1 (25%) | Phase 2 (50%) | Phase 3 (75%) | Phase 4 (90%) |
|-----------|---------------|---------------|---------------|---------------|
| Domain Entities | 80% | 90% | 95% | 98% |
| Value Objects | 70% | 85% | 90% | 95% |
| Use Cases | 60% | 75% | 85% | 90% |
| Mappers | 40% | 60% | 75% | 85% |
| Repositories | 30% | 50% | 70% | 80% |

### Performance Targets

- **Tests Unitaires** : < 100ms par test, < 10s total
- **Tests Intégration** : < 1s par test, < 60s total  
- **Tests E2E** : < 5s par test, < 300s total

### Quality Gates

```python
# Dans pytest.ini
--cov-fail-under=25  # Phase actuelle
--durations=10       # Track des tests lents
--tb=short          # Traceback concis
```

## Stratégies de Test par Couche

### Domain Layer (Priority: HIGH)

**Entities** - Test des règles métier
- Validation des invariants
- Calculs métier (PnL, returns, etc.)
- Events domain
- State transitions

**Value Objects** - Test d'immutabilité et validation
- Money calculations
- Price validations  
- Signal generation

### Application Layer (Priority: HIGH)

**Use Cases** - Test d'orchestration
- Happy path scenarios
- Error handling
- Business rule enforcement
- Event publishing

**Mappers** - Test de conversion
- Entity ↔ DTO mapping
- Data transformation
- Null handling

### Infrastructure Layer (Priority: MEDIUM)

**Repositories** - Test de persistance
- CRUD operations
- Query correctness
- Transaction handling
- Connection management

**External Services** - Test d'intégration
- API calls
- Data mapping
- Error handling
- Circuit breaker

## Outils et Configuration

### Dependencies

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
pytest-factoryboy = "^2.6.0"
pytest-xdist = "^3.8.0"
faker = "^22.5.0"
factory-boy = "^3.3.0"
freezegun = "^1.4.0"
httpx = "^0.25.2"
```

### CI/CD Integration

```yaml
# Dans CI pipeline
- name: Run Tests
  run: |
    pytest -m "unit" --cov=src --cov-report=xml
    pytest -m "integration and database" --cov-append
    pytest -m "contract" --cov-append
```

## Bonnes Pratiques

### DO ✅

- **Isoler les tests** : Chaque test indépendant
- **Nommer explicitement** : `test_should_do_something_when_condition`
- **Tester les edge cases** : Null values, empty collections, limits
- **Utiliser des factories** : Données cohérentes et réalistes
- **Mocker les dépendances** : Tests unitaires purs
- **Tester les erreurs** : Validation des exceptions métier

### DON'T ❌

- **Tests couplés** : Dépendance à l'ordre d'exécution
- **Hard-coded values** : Dates, IDs, prix fixes
- **Tests trop larges** : Plus de 5-10 asserts
- **Mocking excessif** : Mock de tout dans les tests d'intégration
- **Tests lents** : > 100ms pour unitaires
- **Asserts multiples** : Une seule responsabilité par test

### Test Data Management

```python
# ✅ Bon : Utilisation de factories
def test_portfolio_value_calculation():
    portfolio = PortfolioFactory.create()
    positions = PositionFactory.create_batch(3, portfolio=portfolio)
    
# ❌ Éviter : Données hard-codées
def test_bad_example():
    portfolio = Portfolio(id=uuid.UUID("12345678-1234-5678-9012-123456789012"))
```

---

*Cette documentation doit évoluer avec le projet. Mise à jour à chaque refactoring majeur.*

NB : Tu doit utiliser l'environnement poetry et tu peux installer des dépendances externes si necessaire.