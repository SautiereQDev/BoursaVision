#!/bin/bash
# Script de monitoring du coverage
# Usage: ./scripts/coverage-monitor.sh

echo "🧪 Exécution des tests avec coverage..."
poetry run pytest --cov=src --cov-report=term --cov-report=html --quiet

echo ""
echo "📊 Résumé du coverage:"
echo "- Objectif Phase 1: 65% (Quick wins)"
echo "- Objectif Phase 2: 75% (Modules métier)"
echo "- Objectif Phase 3: 85% (Amélioration)"

echo ""
echo "🎯 Modules prioritaires 0% coverage:"
echo "1. celery_app.py (49 lignes)"
echo "2. cli.py (170 lignes)"
echo "3. market_data_cache.py (106 lignes)"
echo "4. repositories.py (167 lignes)"

echo ""
echo "📈 Rapport HTML disponible: file://$(pwd)/htmlcov/index.html"
