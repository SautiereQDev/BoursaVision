#!/bin/bash

# Script d'exécution de tests pour BoursaVision
# ============================================
#
# Ce script lance tous les tests avec différents niveaux de couverture
# et génère des rapports détaillés.
#
# Usage :
#     ./run_tests.sh                    # Tests complets avec couverture
#     ./run_tests.sh --fast            # Tests rapides uniquement
#     ./run_tests.sh --unit            # Tests unitaires uniquement
#     ./run_tests.sh --integration     # Tests d'intégration uniquement
#     ./run_tests.sh --e2e             # Tests end-to-end uniquement
#     ./run_tests.sh --coverage-only   # Générer rapport couverture seulement

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}"
COVERAGE_DIR="${BACKEND_DIR}/htmlcov"
REPORTS_DIR="${BACKEND_DIR}/test-reports"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier les prérequis
check_prerequisites() {
    print_header "Vérification des prérequis"
    
    cd "${BACKEND_DIR}"
    
    # Vérifier que nous sommes dans un environnement virtuel
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        print_warning "Aucun environnement virtuel détecté. Utilisation de Poetry..."
        
        if [[ -f "poetry.lock" ]]; then
            export POETRY_VENV_IN_PROJECT=true
        else
            print_error "Fichier poetry.lock non trouvé. Veuillez configurer Poetry."
            exit 1
        fi
    fi
    
    # Vérifier les dépendances de test
    poetry run python -c "import pytest, pytest_asyncio, faker" 2>/dev/null || {
        print_warning "Installation des dépendances de test..."
        poetry install
    }
    
    print_success "Prérequis vérifiés"
}

# Nettoyer les anciens rapports
clean_reports() {
    print_header "Nettoyage des anciens rapports"
    
    cd "${BACKEND_DIR}"
    
    # Supprimer les anciens rapports
    rm -rf "${COVERAGE_DIR}"
    rm -rf "${REPORTS_DIR}"
    rm -f .coverage
    rm -rf .pytest_cache
    
    # Créer les répertoires de rapport
    mkdir -p "${REPORTS_DIR}"
    
    print_success "Rapports nettoyés"
}

# Exécuter les tests unitaires
run_unit_tests() {
    print_header "Tests Unitaires"
    
    cd "${BACKEND_DIR}"
    
    echo "Exécution des tests unitaires..."
    
    PYTHONPATH=src poetry run pytest tests/unit/ tests/test_simple_validation.py \
        -v \
        --tb=short \
        --strict-markers \
        -m "unit or fast" \
        --disable-warnings \
        || {
            print_error "Échec des tests unitaires"
            return 1
        }
    
    print_success "Tests unitaires terminés"
}

# Exécuter les tests d'intégration
run_integration_tests() {
    print_header "Tests d'Intégration"
    
    cd "${BACKEND_DIR}"
    
    echo "Exécution des tests d'intégration..."
    
    PYTHONPATH=src:tests poetry run pytest tests/integration/ \
        -v \
        --tb=short \
        --strict-markers \
        -m "integration" \
        --disable-warnings \
        || {
            print_error "Échec des tests d'intégration"
            return 1
        }
    
    print_success "Tests d'intégration terminés"
}

# Exécuter les tests end-to-end
run_e2e_tests() {
    print_header "Tests End-to-End"
    
    cd "${BACKEND_DIR}"
    
    echo "Exécution des tests end-to-end..."
    
    PYTHONPATH=src poetry run pytest tests/e2e/ \
        -v \
        --tb=short \
        --strict-markers \
        -m "e2e" \
        --disable-warnings \
        || {
            print_error "Échec des tests end-to-end"
            return 1
        }
    
    print_success "Tests end-to-end terminés"
}

# Tests rapides seulement
run_fast_tests() {
    print_header "Tests Rapides"
    
    cd "${BACKEND_DIR}"
    
    echo "Exécution des tests rapides..."
    
    PYTHONPATH=src poetry run pytest \
        -v \
        --tb=short \
        --strict-markers \
        -m "fast and not slow" \
        --disable-warnings \
        || {
            print_error "Échec des tests rapides"
            return 1
        }
    
    print_success "Tests rapides terminés"
}

# Exécuter tous les tests
run_all_tests() {
    print_header "Tests Complets"
    
    cd "${BACKEND_DIR}"
    
    echo "Exécution de tous les tests..."
    
    PYTHONPATH=src poetry run pytest \
        -v \
        --tb=short \
        --strict-markers \
        --disable-warnings \
        || {
            print_error "Échec des tests complets"
            return 1
        }
    
    print_success "Tests complets terminés"
}

# Générer le rapport de couverture combiné
generate_coverage_report() {
    print_header "Rapport de Couverture"
    
    cd "${BACKEND_DIR}"
    
    echo "Les rapports de couverture seront ajoutés plus tard quand le code source sera présent."
    
    print_success "Configuration de couverture prête"
}

# Afficher les statistiques finales
show_statistics() {
    print_header "Statistiques des Tests"
    
    cd "${BACKEND_DIR}"
    
    echo ""
    echo "=== STATISTIQUES ==="
    
    # Compter les tests par type
    unit_tests=$(find tests/unit -name "test_*.py" | wc -l)
    integration_tests=$(find tests/integration -name "test_*.py" | wc -l)
    e2e_tests=$(find tests/e2e -name "test_*.py" | wc -l)
    total_tests=$((unit_tests + integration_tests + e2e_tests))
    
    echo "Tests unitaires:     ${unit_tests} fichiers"
    echo "Tests intégration:   ${integration_tests} fichiers"  
    echo "Tests end-to-end:    ${e2e_tests} fichiers"
    echo "Total:               ${total_tests} fichiers"
    echo ""
    
    # Statistiques de couverture si disponibles
    if [[ -f ".coverage" ]]; then
        coverage report --format=text | grep "TOTAL" || echo "Couverture non disponible"
    fi
    
    echo ""
    echo "Rapports disponibles dans: ${REPORTS_DIR}/"
    echo "Couverture HTML dans: ${COVERAGE_DIR}/"
}

# Fonction principale
main() {
    local command="${1:-all}"
    
    case "$command" in
        --fast)
            check_prerequisites
            clean_reports
            run_fast_tests
            generate_coverage_report
            show_statistics
            ;;
        --unit)
            check_prerequisites
            clean_reports
            run_unit_tests
            generate_coverage_report
            show_statistics
            ;;
        --integration)
            check_prerequisites
            clean_reports
            run_integration_tests
            generate_coverage_report
            show_statistics
            ;;
        --e2e)
            check_prerequisites
            clean_reports
            run_e2e_tests
            generate_coverage_report
            show_statistics
            ;;
        --coverage-only)
            generate_coverage_report
            show_statistics
            ;;
        --help|-h)
            echo "Usage: $0 [--fast|--unit|--integration|--e2e|--coverage-only|--help]"
            echo ""
            echo "Options:"
            echo "  (no args)         Exécuter tous les tests"
            echo "  --fast           Tests rapides uniquement"
            echo "  --unit           Tests unitaires uniquement"
            echo "  --integration    Tests d'intégration uniquement"
            echo "  --e2e            Tests end-to-end uniquement"
            echo "  --coverage-only  Générer rapport couverture seulement"
            echo "  --help           Afficher cette aide"
            ;;
        all|*)
            check_prerequisites
            clean_reports
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            generate_coverage_report
            show_statistics
            ;;
    esac
    
    echo ""
    print_success "Tests terminés avec succès!"
    echo ""
    echo "Pour voir les résultats:"
    echo "  - Rapport HTML: open ${COVERAGE_DIR}/index.html"
    echo "  - Rapports XML: ls ${REPORTS_DIR}/"
    echo ""
}

# Point d'entrée
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
