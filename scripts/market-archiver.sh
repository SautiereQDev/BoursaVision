#!/bin/bash

# Market Data Archiver Controller
# This script provides easy access to the market data archiving system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "📊 Boursa Vision - Market Data Archiver"
echo "========================================"

# Function to run market data archiver
archive_data() {
    echo "🚀 Starting market data archival..."
    
    if docker exec boursa-backend /bin/bash -c "cd /app && PYTHONPATH=/app/src poetry run python -m boursa_vision.application.services.archiving.market_archiver"; then
        echo "✅ Market data archival completed successfully"
        return 0
    else
        echo "❌ Market data archival failed"
        return 1
    fi
}

# Function to check data quality
check_quality() {
    echo "🔍 Checking data quality..."
    
    echo "📈 Data Quality Summary:"
    docker exec boursa-postgres psql -U boursa_user -d boursa_vision -c "
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT symbol) as unique_symbols,
            COUNT(DISTINCT data_source) as data_sources,
            MIN(timestamp) as oldest_data,
            MAX(timestamp) as newest_data
        FROM market_data_archive;
    " 2>/dev/null || echo "⚠️  Unable to retrieve statistics"
    
    echo -e "\n🔍 Quality Issues (should be empty):"
    docker exec boursa-postgres psql -U boursa_user -d boursa_vision -c "
        SELECT * FROM v_data_quality_monitor 
        WHERE record_count > 1 OR distinct_close_prices > 1 
        LIMIT 10;
    " 2>/dev/null || echo "⚠️  Unable to check quality issues"
}

# Function to show detailed statistics
detailed_stats() {
    echo "📊 Detailed Archive Statistics:"
    
    echo -e "\n📈 Records by Symbol:"
    docker exec boursa-postgres psql -U boursa_user -d boursa_vision -c "
        SELECT 
            symbol,
            COUNT(*) as records,
            MIN(timestamp) as oldest,
            MAX(timestamp) as newest,
            data_source
        FROM market_data_archive 
        GROUP BY symbol, data_source 
        ORDER BY records DESC;
    " 2>/dev/null || echo "⚠️  Unable to retrieve detailed statistics"
    
    echo -e "\n🕐 Data Timeline:"
    docker exec boursa-postgres psql -U boursa_user -d boursa_vision -c "
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as records,
            COUNT(DISTINCT symbol) as symbols
        FROM market_data_archive 
        GROUP BY DATE(timestamp) 
        ORDER BY date DESC 
        LIMIT 10;
    " 2>/dev/null || echo "⚠️  Unable to retrieve timeline data"
}

# Function to compare old vs new archiver
compare_methods() {
    echo "⚖️  Comparing archiving methods..."
    
    echo "🔄 Running old archiver first..."
    if docker exec boursa-backend poetry run python simple_archiver.py > /tmp/old_archiver.log 2>&1; then
        old_added=$(grep "Total:" /tmp/old_archiver.log | awk '{print $2}' | head -1)
        echo "📊 Old archiver: $old_added records added"
    else
        echo "❌ Old archiver failed"
    fi
    
    echo -e "\n🔄 Running market data archiver..."
    if archive_data > /tmp/archiver.log 2>&1; then
        echo "✅ Market data archiver completed - check logs for details"
    else
        echo "❌ Market data archiver failed"
    fi
}

# Function to check services
check_services() {
    if ! docker ps | grep -q boursa-backend; then
        echo "❌ Backend container is not running"
        return 1
    fi
    
    if ! docker ps | grep -q boursa-postgres; then
        echo "❌ PostgreSQL container is not running"
        return 1
    fi
    
    return 0
}

# Main execution
main() {
    local command="${1:-archive}"
    
    case "$command" in
        "archive"|"run")
            if check_services; then
                archive_data
            else
                echo "❌ Required services are not running"
                exit 1
            fi
            ;;
        "quality"|"check")
            if check_services; then
                check_quality
            else
                echo "❌ Required services are not running"
                exit 1
            fi
            ;;
        "stats"|"statistics")
            if check_services; then
                detailed_stats
            else
                echo "❌ Required services are not running"
                exit 1
            fi
            ;;
        "compare")
            if check_services; then
                compare_methods
            else
                echo "❌ Required services are not running"
                exit 1
            fi
            ;;
        "monitor")
            echo "🔄 Starting continuous monitoring..."
            while true; do
                if check_services; then
                    archive_data
                    echo "⏰ Next market data archival in 24 hours..."
                    sleep 86400  # 24 hours (86400 seconds)
                else
                    echo "❌ Services not available, retrying in 1 minute..."
                    sleep 60
                fi
            done
            ;;
        "help"|"--help"|"-h")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  archive          Run market data archival with pattern validation (default)"
            echo "  quality          Check data quality and show issues"
            echo "  stats            Show detailed archive statistics"
            echo "  compare          Compare archiving methods"
            echo "  monitor          Run continuous market data archival every 24 hours"
            echo "  help             Show this help message"
            echo ""
            echo "Features:"
            echo "  ✅ Pattern-based validation"
            echo "  ✅ Fuzzy duplicate detection"
            echo "  ✅ Data normalization"
            echo "  ✅ Quality monitoring"
            echo "  ✅ Source tracking"
            ;;
        *)
            echo "❌ Unknown command: $command"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
