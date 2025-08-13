#!/bin/bash

# Boursa Vision - Backup Script
# Automated backup system for database and application data

set -e

# Configuration
PROJECT_DIR="/opt/boursa-vision"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="/var/log/boursa-backup.log"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# Function to send notification (you can integrate with email, Slack, etc.)
send_notification() {
    local message="$1"
    local status="$2"
    
    log_message "$message"
    
    # Example: Send email notification (uncomment and configure)
    # echo "$message" | mail -s "Boursa Vision Backup - $status" admin@yourdomain.com
    
    # Example: Send to webhook/Slack (uncomment and configure)
    # curl -X POST -H 'Content-type: application/json' \
    #     --data "{\"text\":\"$message\"}" \
    #     YOUR_WEBHOOK_URL
}

# Function to check if docker containers are running
check_containers() {
    local containers=("boursa-postgres-prod" "boursa-redis-prod")
    
    for container in "${containers[@]}"; do
        if ! docker ps | grep -q $container; then
            log_message "ERROR: Container $container is not running!"
            return 1
        fi
    done
    
    return 0
}

# Function to backup database
backup_database() {
    local timestamp="$1"
    local backup_file="$BACKUP_DIR/database_$timestamp.sql.gz"
    
    log_message "Starting database backup..."
    
    # Create database backup
    if docker exec boursa-postgres-prod pg_dump -U $POSTGRES_USER -d $POSTGRES_DB | gzip > $backup_file; then
        log_message "Database backup completed: $backup_file"
        
        # Verify backup file
        if [[ -f "$backup_file" ]] && [[ $(stat -c%s "$backup_file") -gt 1000 ]]; then
            log_message "Database backup verification successful"
            return 0
        else
            log_message "ERROR: Database backup verification failed - file too small or missing"
            return 1
        fi
    else
        log_message "ERROR: Database backup failed"
        return 1
    fi
}

# Function to backup docker volumes
backup_volumes() {
    local timestamp="$1"
    local volumes=("boursa_postgres_data" "boursa_redis_data" "boursa_backend_logs")
    
    log_message "Starting volumes backup..."
    
    for volume in "${volumes[@]}"; do
        local backup_file="$BACKUP_DIR/${volume}_$timestamp.tar.gz"
        
        if docker run --rm -v $volume:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/$(basename $backup_file) -C /data .; then
            log_message "Volume backup completed: $volume -> $backup_file"
        else
            log_message "ERROR: Volume backup failed for $volume"
            return 1
        fi
    done
    
    return 0
}

# Function to cleanup old backups
cleanup_old_backups() {
    log_message "Starting cleanup of old backups (older than $RETENTION_DAYS days)..."
    
    local deleted_count=0
    
    # Find and delete old backup files
    while IFS= read -r -d '' file; do
        rm "$file"
        deleted_count=$((deleted_count + 1))
        log_message "Deleted old backup: $(basename "$file")"
    done < <(find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    if [[ $deleted_count -gt 0 ]]; then
        log_message "Cleanup completed: $deleted_count old backups deleted"
    else
        log_message "Cleanup completed: no old backups found"
    fi
}

# Main backup function
run_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local overall_status="SUCCESS"
    local errors=0
    
    log_message "=========================================="
    log_message "Starting Boursa Vision backup process"
    log_message "Timestamp: $timestamp"
    log_message "=========================================="
    
    # Check if containers are running
    if ! check_containers; then
        send_notification "ERROR: Required containers are not running. Backup aborted." "FAILED"
        exit 1
    fi
    
    # Source environment variables
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        source $PROJECT_DIR/.env
    else
        log_message "WARNING: .env file not found, using default values"
    fi
    
    # Perform backups
    backup_database "$timestamp" || errors=$((errors + 1))
    backup_volumes "$timestamp" || errors=$((errors + 1))
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Determine overall status
    if [[ $errors -gt 0 ]]; then
        overall_status="FAILED"
        log_message "Backup completed with $errors error(s)"
    else
        log_message "Backup completed successfully"
    fi
    
    # Send notification
    local backup_size=$(du -sh $BACKUP_DIR 2>/dev/null | cut -f1 || echo "Unknown")
    send_notification "Boursa Vision backup $overall_status. Errors: $errors. Total backup size: $backup_size" "$overall_status"
    
    log_message "=========================================="
    log_message "Backup process completed: $overall_status"
    log_message "=========================================="
    
    return $errors
}

# Parse command line arguments
case "${1:-backup}" in
    backup)
        run_backup
        ;;
    cleanup)
        cleanup_old_backups
        ;;
    help|--help|-h)
        echo "Boursa Vision Backup Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  backup    Create full backup (default)"
        echo "  cleanup   Remove old backups"
        echo "  help      Show this help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
