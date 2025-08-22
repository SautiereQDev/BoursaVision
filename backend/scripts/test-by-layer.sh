#!/bin/bash
# Script pour tests par catégories

case "$1" in
  "services")
    echo "🔧 Testing Application Services..."
    poetry run pytest tests/unit/application/services/ -v --tb=short --disable-warnings
    ;;
  "domain")
    echo "🏗️ Testing Domain Layer..."
    poetry run pytest tests/unit/domain/ -v --tb=short --disable-warnings
    ;;
  "infra")
    echo "📦 Testing Infrastructure..."
    poetry run pytest tests/unit/infrastructure/ -v --tb=short --disable-warnings
    ;;
  "integration")
    echo "🔗 Testing Integration..."
    poetry run pytest tests/integration/ -v --tb=short --disable-warnings
    ;;
  "priority1")
    echo "⭐ Testing Priority #1 Services..."
    poetry run pytest \
        tests/unit/application/services/test_authentication_service_complete.py \
        tests/unit/application/services/test_market_data_cache_service.py \
        tests/unit/application/services/test_investment_intelligence.py \
        tests/unit/application/services/test_risk_assessment.py \
        -v --cov=boursa_vision.application.services \
        --cov-report=term-missing:skip-covered \
        --tb=short --disable-warnings
    ;;
  "coverage")
    echo "📊 Testing with Coverage (Services only)..."
    poetry run pytest tests/unit/application/services/ \
        --cov=boursa_vision.application.services \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        -q --tb=line
    ;;
  *)
    echo "Usage: $0 {services|domain|infra|integration|priority1|coverage}"
    echo ""
    echo "  services    - Test tous les services"
    echo "  domain      - Test la couche domaine"
    echo "  infra       - Test l'infrastructure" 
    echo "  integration - Test l'intégration"
    echo "  priority1   - Test services Priority #1 avec couverture"
    echo "  coverage    - Test services avec couverture complète"
    exit 1
    ;;
esac
