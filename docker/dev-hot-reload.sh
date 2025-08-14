#!/bin/bash
# Boursa Vision - Script de développement avec Hot Reload
# Usage: ./dev-hot-reload.sh [action]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction pour vérifier les prérequis
check_requirements() {
    log_info "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    if [ ! -f "$DOCKER_DIR/.env" ]; then
        log_error "Fichier .env manquant dans $DOCKER_DIR"
        log_info "Copiez .env.example vers .env et configurez-le"
        exit 1
    fi
    
    log_success "Prérequis vérifiés"
}

# Fonction pour démarrer les services avec hot reload
start_dev() {
    log_info "🔥 Démarrage en mode développement avec Hot Reload"
    
    cd "$DOCKER_DIR"
    
    # Arrêter les services existants
    docker-compose -f docker-compose.dev.yml down
    
    # Démarrer les services de base (DB, Redis)
    log_info "Démarrage des services de base..."
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    
    # Attendre que la DB soit prête
    log_info "Attente que la base de données soit prête..."
    sleep 10
    
    # Démarrer le backend avec hot reload
    log_info "Démarrage du backend avec hot reload..."
    docker-compose -f docker-compose.dev.yml up backend
}

# Fonction pour redémarrer seulement le backend
restart_backend() {
    log_info "🔄 Redémarrage du backend seulement"
    
    cd "$DOCKER_DIR"
    docker-compose -f docker-compose.dev.yml restart backend
}

# Fonction pour voir les logs
show_logs() {
    cd "$DOCKER_DIR"
    docker-compose -f docker-compose.dev.yml logs -f backend
}

# Fonction pour entrer dans le container backend
shell_backend() {
    log_info "🐚 Ouverture d'un shell dans le container backend"
    cd "$DOCKER_DIR"
    docker-compose -f docker-compose.dev.yml exec backend bash
}

# Fonction pour arrêter tous les services
stop_all() {
    log_info "🛑 Arrêt de tous les services"
    cd "$DOCKER_DIR"
    docker-compose -f docker-compose.dev.yml down
}

# Fonction pour nettoyer les containers et volumes
clean_all() {
    log_warning "🧹 Nettoyage complet (containers, images, volumes)"
    read -p "Êtes-vous sûr ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$DOCKER_DIR"
        docker-compose -f docker-compose.dev.yml down -v --rmi all
        docker system prune -f
        log_success "Nettoyage terminé"
    else
        log_info "Nettoyage annulé"
    fi
}

# Fonction pour tester l'API
test_api() {
    log_info "🧪 Test de l'API"
    
    # Attendre que l'API soit prête
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API accessible"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "API non accessible après 30 tentatives"
            exit 1
        fi
        sleep 1
    done
    
    # Tester quelques endpoints
    echo "📊 Status de santé:"
    curl -s http://localhost:8000/health | jq .
    
    echo -e "\n📈 Test des recommandations:"
    curl -s "http://localhost:8000/recommendations/best-investments?min_score=45&max_recommendations=3" | jq '.recommendations[0:2]'
}

# Fonction pour afficher l'aide
show_help() {
    echo "🚀 Boursa Vision - Script de développement avec Hot Reload"
    echo ""
    echo "Usage: $0 [action]"
    echo ""
    echo "Actions disponibles:"
    echo "  start     - Démarrer tous les services avec hot reload (défaut)"
    echo "  restart   - Redémarrer seulement le backend" 
    echo "  logs      - Afficher les logs du backend"
    echo "  shell     - Ouvrir un shell dans le container backend"
    echo "  stop      - Arrêter tous les services"
    echo "  clean     - Nettoyer containers et volumes"
    echo "  test      - Tester l'API"
    echo "  help      - Afficher cette aide"
    echo ""
    echo "🔥 Hot Reload activé:"
    echo "  - Modifications des fichiers .py détectées automatiquement"
    echo "  - Redémarrage automatique du serveur FastAPI"
    echo "  - Logs en temps réel"
    echo ""
    echo "📁 Fichiers surveillés:"
    echo "  - backend/src/**/*.py"
    echo "  - backend/main.py"
    echo "  - backend/alembic/**/*.py"
}

# Fonction principale
main() {
    case "${1:-start}" in
        "start")
            check_requirements
            start_dev
            ;;
        "restart")
            restart_backend
            ;;
        "logs")
            show_logs
            ;;
        "shell")
            shell_backend
            ;;
        "stop")
            stop_all
            ;;
        "clean")
            clean_all
            ;;
        "test")
            test_api
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Action inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Gestion des signaux pour un arrêt propre
trap 'log_info "Arrêt demandé..."; stop_all; exit 0' INT TERM

# Point d'entrée
main "$@"
