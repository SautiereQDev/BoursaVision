#!/bin/bash

# Boursa Vision - Deployment Script
# This script handles deployment to production

set -e

PROJECT_DIR="/opt/boursa-vision"
DOCKER_DIR="$PROJECT_DIR/docker"
BACKUP_DIR="$PROJECT_DIR/backups"

echo "🚀 Starting Boursa Vision deployment..."

# Function to display help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -e, --env FILE      Environment file (default: .env)"
    echo "  -b, --backup        Create backup before deployment"
    echo "  -r, --rollback      Rollback to previous version"
    echo "  --no-build          Skip building images"
    echo "  --production        Use production configuration"
    echo ""
    echo "Examples:"
    echo "  $0 --production --backup"
    echo "  $0 --rollback"
}

# Default values
ENV_FILE=".env"
CREATE_BACKUP=false
ROLLBACK=false
BUILD_IMAGES=true
PRODUCTION=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--env)
            ENV_FILE="$2"
            shift 2
            ;;
        -b|--backup)
            CREATE_BACKUP=true
            shift
            ;;
        -r|--rollback)
            ROLLBACK=true
            shift
            ;;
        --no-build)
            BUILD_IMAGES=false
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Change to project directory
cd $PROJECT_DIR

# Check if environment file exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ Environment file $ENV_FILE not found!"
    echo "Please copy .env.template to $ENV_FILE and configure it."
    exit 1
fi

# Source environment variables
source $ENV_FILE

# Function to create backup
create_backup() {
    echo "💾 Creating backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/deployment_$TIMESTAMP"
    
    mkdir -p $BACKUP_PATH
    
    # Backup database
    if docker ps | grep -q boursa-postgres-prod; then
        echo "📊 Backing up database..."
        docker exec boursa-postgres-prod pg_dump -U $POSTGRES_USER -d $POSTGRES_DB | gzip > $BACKUP_PATH/database.sql.gz
    fi
    
    # Backup docker volumes
    echo "📁 Backing up volumes..."
    docker run --rm -v boursa_postgres_data:/data -v $BACKUP_PATH:/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
    docker run --rm -v boursa_redis_data:/data -v $BACKUP_PATH:/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
    
    # Save current docker-compose configuration
    cp $DOCKER_DIR/docker-compose.prod.yml $BACKUP_PATH/
    
    echo "✅ Backup created at $BACKUP_PATH"
    echo $BACKUP_PATH > $BACKUP_DIR/latest_backup.txt
}

# Function to rollback
rollback_deployment() {
    echo "🔄 Rolling back deployment..."
    
    if [[ ! -f "$BACKUP_DIR/latest_backup.txt" ]]; then
        echo "❌ No backup found for rollback!"
        exit 1
    fi
    
    LATEST_BACKUP=$(cat $BACKUP_DIR/latest_backup.txt)
    
    if [[ ! -d "$LATEST_BACKUP" ]]; then
        echo "❌ Backup directory not found: $LATEST_BACKUP"
        exit 1
    fi
    
    echo "📁 Stopping current services..."
    cd $DOCKER_DIR
    docker-compose -f docker-compose.prod.yml down
    
    echo "📊 Restoring database..."
    docker-compose -f docker-compose.prod.yml up -d postgres redis
    sleep 10
    
    # Restore database
    if [[ -f "$LATEST_BACKUP/database.sql.gz" ]]; then
        zcat $LATEST_BACKUP/database.sql.gz | docker exec -i boursa-postgres-prod psql -U $POSTGRES_USER -d $POSTGRES_DB
    fi
    
    echo "🚀 Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "✅ Rollback completed!"
    exit 0
}

# Handle rollback
if [[ "$ROLLBACK" == true ]]; then
    rollback_deployment
fi

# Create backup if requested
if [[ "$CREATE_BACKUP" == true ]]; then
    create_backup
fi

# Update repository
echo "📥 Updating repository..."
git fetch origin
git reset --hard origin/main

# Build images if needed
if [[ "$BUILD_IMAGES" == true ]]; then
    echo "🔨 Building Docker images..."
    cd $DOCKER_DIR
    
    if [[ "$PRODUCTION" == true ]]; then
        docker-compose -f docker-compose.prod.yml build --no-cache
    else
        docker-compose -f docker-compose.dev.yml build --no-cache
    fi
fi

# Run database migrations
echo "🗄️ Running database migrations..."
cd $DOCKER_DIR

if [[ "$PRODUCTION" == true ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    COMPOSE_FILE="docker-compose.dev.yml"
fi

# Start database first
docker-compose -f $COMPOSE_FILE up -d postgres redis
echo "⏳ Waiting for database to be ready..."
sleep 15

# Run migrations
docker-compose -f $COMPOSE_FILE run --rm backend poetry run alembic upgrade head

# Deploy services
echo "🚀 Deploying services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Health checks
echo "🏥 Running health checks..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80 || echo "000")

if [[ "$BACKEND_HEALTH" == "200" ]]; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed (HTTP $BACKEND_HEALTH)"
fi

if [[ "$FRONTEND_HEALTH" == "200" ]]; then
    echo "✅ Frontend health check passed"
else
    echo "❌ Frontend health check failed (HTTP $FRONTEND_HEALTH)"
fi

# Show deployment status
echo ""
echo "📊 Deployment Status:"
echo "===================="
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "📋 Container Logs (last 20 lines):"
echo "=================================="
echo "Backend:"
docker-compose -f $COMPOSE_FILE logs --tail=20 backend

echo ""
echo "✅ Deployment completed!"
echo ""
echo "🔗 Service URLs:"
if [[ "$PRODUCTION" == true ]]; then
    echo "   Frontend: https://$(hostname -f)"
    echo "   API: https://$(hostname -f)/api/v1"
    echo "   Documentation: https://$(hostname -f)/docs"
    echo "   WebSocket: wss://$(hostname -f)/ws"
else
    echo "   Frontend: http://localhost:3000"
    echo "   API: http://localhost:8000/api/v1"
    echo "   Documentation: http://localhost:8000/docs"
    echo "   WebSocket: ws://localhost:8000/ws"
fi
echo ""
echo "📁 Useful commands:"
echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f [service]"
echo "   Restart: docker-compose -f $COMPOSE_FILE restart [service]"
echo "   Scale workers: docker-compose -f $COMPOSE_FILE up -d --scale celery-worker=3"
echo ""

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

echo "🎉 Deployment script completed successfully!"
