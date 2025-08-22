#!/bin/bash
# Script pour exécuter seulement les tests rapides et importants

echo "🚀 Tests rapides - Services critiques seulement"

# Tests des services avec priorité 1 seulement
poetry run pytest \
    tests/unit/application/services/test_authentication_service_complete.py \
    tests/unit/application/services/test_market_data_cache_service.py \
    tests/unit/application/services/test_investment_intelligence.py \
    -v --cov=boursa_vision.application.services \
    --cov-report=term-missing:skip-covered \
    --tb=short \
    --disable-warnings \
    --maxfail=3

echo ""
echo "✅ Tests critiques terminés!"
echo "Pour tous les tests: poetry run pytest"
echo "Pour un service spécifique: poetry run pytest tests/unit/application/services/test_SERVICE.py"
