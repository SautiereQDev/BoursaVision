gh issue create \
  --title "🧪 Test Architecture Audit & Optimization - Current State vs Target" \
  --body "## 📋 Summary

Complete audit of the current BoursaVision backend test architecture and optimization plan to achieve standards defined in \`TESTS.md\`.

## 🔍 Current Test State

### 📊 Global Metrics
- **Total test files**: 136 Python files
- **Unit tests** (domain): 18 files ✅ 
- **Integration tests**: 7 files ⚠️
- **E2E tests**: 1 file ❌ (insufficient)
- **Factories**: Empty (only \`__init__.py\`) ❌

### 🗂️ Current vs Target Structure

#### ✅ Positive Points
- **Clean Architecture respected**: domain/application/infrastructure separation
- **Pytest markers**: Correct usage of \`@pytest.mark.unit\`
- **Complete documentation**: \`TESTS.md\` very well structured
- **Stability**: Problematic tests isolated (.disabled/.backup files)

#### ⚠️ Identified Gaps

**Missing folder structure:**
\`\`\`diff
tests/
├── ✅ unit/domain/          # 18 files (GOOD)
├── ❌ unit/entities/        # MISSING from TESTS.md spec
├── ❌ unit/value_objects/   # MISSING from TESTS.md spec  
├── ⚠️ integration/          # 7 files (INSUFFICIENT)
├── ❌ e2e/                  # Only 1 file (CRITICAL)
├── ❌ factories/            # EMPTY (factory-boy not implemented)
└── ✅ fixtures/             # Present but partial
\`\`\`

**Disabled tests (recent stabilization):**
- \`test_market_archiver_real.py.disabled\`
- \`test_market_data_cache_real.py.disabled\`
- \`test_archived_market_data_repository.py.disabled\`
- \`test_market_api_enhanced.py.disabled\`

## 🎯 Priority Action Plan

### Phase 1: Infrastructure (2-3 days) 🔥
- [ ] **Implement Factory Classes** with \`factory-boy\` + \`faker\`
  - \`InvestmentFactory\`, \`PortfolioFactory\`, \`UserFactory\`
  - \`MarketDataFactory\` for realistic data
- [ ] **Restructure fixtures** according to TESTS.md spec
- [ ] **Clean disabled tests** (analysis + reactivation or definitive removal)

### Phase 2: Domain Coverage (3-4 days) 🔥
- [ ] **Value Objects Tests**: Money, Price, Currency, Signal
- [ ] **Entity Tests**: Investment, Portfolio, Position
- [ ] **Domain Services Tests**: Business calculations, validation rules
- [ ] **Target**: 90% coverage domain layer

### Phase 3: Integration Tests (2-3 days) ⚠️
- [ ] **Repository Tests**: CRUD + complex queries with real DB
- [ ] **Mapper Tests**: Entity ↔ DTO transformations
- [ ] **Use Cases Integration**: Tests with real dependencies
- [ ] **Target**: 75% coverage application layer

### Phase 4: E2E Tests (2 days) ❌
- [ ] **User Journeys**: Portfolio creation → Investment → Analysis
- [ ] **API Workflows**: Authentication → Operations → Results
- [ ] **Error Scenarios**: Timeout, network, auth failures

## 📐 Quality Standards Targets

### Progressive Coverage (according to TESTS.md)
| Component | Phase 1 (25%) | **Phase 2 (50%)** | Phase 3 (75%) | Phase 4 (90%) |
|-----------|---------------|-------------------|---------------|---------------|
| Domain Entities | 80% | **90%** ⭐ | 95% | 98% |
| Value Objects | 70% | **85%** ⭐ | 90% | 95% |
| Use Cases | 60% | **75%** ⭐ | 85% | 90% |
| Repositories | 30% | **50%** ⭐ | 70% | 80% |

### Performance Targets
- **Unit Tests**: < 100ms per test
- **Integration Tests**: < 1s per test  
- **E2E Tests**: < 5s per test

## 🛠️ Immediate Technical Actions

### 1. Setup Factory Pattern
\`\`\`python
# Create tests/factories/investment_factory.py
class InvestmentFactory(factory.Factory):
    class Meta:
        model = Investment
    
    symbol = factory.Faker('stock_symbol')
    name = factory.Faker('company')
    sector = factory.Faker('random_element', elements=list(InvestmentSector))
\`\`\`

### 2. Restructure Fixtures
\`\`\`python
# tests/fixtures/auth_fixtures.py
@pytest.fixture(scope=\"session\")
async def authenticated_user():
    return UserFactory.create()
\`\`\`

### 3. Implement Complete Markers
\`\`\`python
# Tests with markers according to TESTS.md
@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.portfolio
def test_should_calculate_portfolio_value():
\`\`\`

## 🎛️ Target Execution Commands

\`\`\`bash
# Tests by type
pytest -m unit           # Fast unit tests
pytest -m integration    # Integration tests with DB
pytest -m e2e           # End-to-end tests

# Tests by domain  
pytest -m portfolio     # Portfolio tests
pytest -m investment    # Investment tests

# Coverage with targets
pytest --cov=src/boursa_vision --cov-report=html --cov-fail-under=50
\`\`\`

## 📋 Acceptance Criteria

- [ ] **136+ tests** organized according to TESTS.md architecture
- [ ] **50% minimum coverage** on domain + application layers
- [ ] **Functional factories** for all domain models
- [ ] **0 disabled tests** (reactivated or properly removed)
- [ ] **CI/CD pipeline** with parallel tests and coverage reports
---

**Total estimation**: 8-12 development days  
**Impact**: Massive improvement in code quality, reliability and maintainability  
**ROI**: Robust tests → fewer bugs → faster development" \
  --label "testing" \
  --label "architecture" \
  --label "technical-debt" \
  --label "enhancement" \
  --label "priority:high" \
  --label "domain" \
  --label "clean-architecture" \
  --assignee "@me"