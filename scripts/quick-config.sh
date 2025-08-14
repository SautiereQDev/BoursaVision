#!/bin/bash

# Quick Archiver Configuration Script
# Usage: ./scripts/quick-config.sh [preset]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "⚙️  Market Data Archiver - Quick Configuration"
echo "====================================================="

# Function to show available presets
show_presets() {
    echo "📋 Available Presets:"
    echo ""
    echo "🚀 intraday   - 5 minute intervals, 1 day period, 5 min monitoring"
    echo "📊 daily      - Daily intervals, 30 day period, 1 hour monitoring (DEFAULT)"
    echo "📅 weekly     - Weekly intervals, 6 month period, daily monitoring"
    echo "📈 monthly    - Monthly intervals, 2 year period, daily monitoring"
    echo "🔧 custom     - Configure manually"
    echo ""
}

# Function to apply preset
apply_preset() {
    local preset="$1"
    
    case "$preset" in
        "intraday")
            INTERVAL="5m"
            PERIOD="1d"
            MONITOR_SECONDS="300"
            MONITOR_DESC="5 minutes"
            ;;
        "daily")
            INTERVAL="1d"
            PERIOD="30d"
            MONITOR_SECONDS="3600"
            MONITOR_DESC="1 hour"
            ;;
        "weekly")
            INTERVAL="1wk"
            PERIOD="6mo"
            MONITOR_SECONDS="86400"
            MONITOR_DESC="24 hours"
            ;;
        "monthly")
            INTERVAL="1mo"
            PERIOD="2y"
            MONITOR_SECONDS="86400"
            MONITOR_DESC="24 hours"
            ;;
        "custom")
            configure_custom
            return
            ;;
        *)
            echo "❌ Unknown preset: $preset"
            show_presets
            return 1
            ;;
    esac
    
    echo "🎯 Applying '$preset' preset..."
    echo "   📊 Data Interval: $INTERVAL"
    echo "   📅 Data Period: $PERIOD"
    echo "   ⏰ Monitoring: $MONITOR_DESC"
    echo ""
    
    apply_configuration
}

# Function for custom configuration
configure_custom() {
    echo "🔧 Custom Configuration"
    echo ""
    
    echo "📊 Data Interval Options:"
    echo "   1m, 5m, 15m, 30m, 1h (intraday)"
    echo "   1d, 5d (daily)"
    echo "   1wk (weekly)"
    echo "   1mo, 3mo (monthly)"
    echo ""
    read -p "Enter data interval [1d]: " INTERVAL
    INTERVAL="${INTERVAL:-1d}"
    
    echo ""
    echo "📅 Data Period Options:"
    echo "   1d, 5d, 7d (short term)"
    echo "   1mo, 3mo, 6mo (medium term)"
    echo "   1y, 2y, 5y, max (long term)"
    echo ""
    read -p "Enter data period [30d]: " PERIOD
    PERIOD="${PERIOD:-30d}"
    
    echo ""
    echo "⏰ Monitoring Interval Options:"
    echo "   300 (5 minutes), 600 (10 minutes)"
    echo "   1800 (30 minutes), 3600 (1 hour)"
    echo "   14400 (4 hours), 86400 (24 hours)"
    echo ""
    read -p "Enter monitoring interval in seconds [3600]: " MONITOR_SECONDS
    MONITOR_SECONDS="${MONITOR_SECONDS:-3600}"
    
    # Calculate description
    if [ "$MONITOR_SECONDS" -ge 3600 ]; then
        MONITOR_DESC="$((MONITOR_SECONDS / 3600)) hour(s)"
    elif [ "$MONITOR_SECONDS" -ge 60 ]; then
        MONITOR_DESC="$((MONITOR_SECONDS / 60)) minute(s)"
    else
        MONITOR_DESC="$MONITOR_SECONDS second(s)"
    fi
    
    echo ""
    echo "🎯 Custom configuration:"
    echo "   📊 Data Interval: $INTERVAL"
    echo "   📅 Data Period: $PERIOD"
    echo "   ⏰ Monitoring: $MONITOR_DESC"
    echo ""
    
    apply_configuration
}

# Function to apply configuration
apply_configuration() {
    echo "🔄 Updating configuration files..."
    
    # Update market_archiver.py
    ARCHIVER_FILE="$PROJECT_ROOT/backend/market_archiver.py"
    if [ -f "$ARCHIVER_FILE" ]; then
        # Create backup
        cp "$ARCHIVER_FILE" "$ARCHIVER_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Update configuration
        sed -i "s/interval='[^']*'/interval='$INTERVAL'/g" "$ARCHIVER_FILE"
        sed -i "s/period='[^']*'/period='$PERIOD'/g" "$ARCHIVER_FILE"
        
        echo "✅ Updated $ARCHIVER_FILE"
    else
        echo "❌ Archiver file not found: $ARCHIVER_FILE"
    fi
    
    # Update market-archiver.sh
    SCRIPT_FILE="$PROJECT_ROOT/scripts/market-archiver.sh"
    if [ -f "$SCRIPT_FILE" ]; then
        # Create backup
        cp "$SCRIPT_FILE" "$SCRIPT_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Update monitoring interval
        sed -i "s/sleep [0-9]*  # .*/sleep $MONITOR_SECONDS  # $MONITOR_DESC ($MONITOR_SECONDS seconds)/g" "$SCRIPT_FILE"
        sed -i "s/Next market data archival in [^.]*/Next market data archival in $MONITOR_DESC/g" "$SCRIPT_FILE"
        sed -i "s/Run continuous market data archival every [^\"]*\"/Run continuous market data archival every $MONITOR_DESC\"/g" "$SCRIPT_FILE"
        
        echo "✅ Updated $SCRIPT_FILE"
    else
        echo "❌ Script file not found: $SCRIPT_FILE"
    fi
    
    echo ""
    echo "🎉 Configuration applied successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Test new configuration: ./scripts/market-archiver.sh archive"
    echo "   2. Start monitoring: ./scripts/market-archiver.sh monitor"
    echo "   3. Check quality: ./scripts/market-archiver.sh quality"
    echo ""
    echo "📄 Backup files created with timestamp for safety"
}

# Main execution
main() {
    local preset="${1:-daily}"
    
    case "$preset" in
        "help"|"--help"|"-h")
            show_presets
            echo "Usage: $0 [preset]"
            echo ""
            echo "Examples:"
            echo "  $0 daily      # Apply daily preset (default)"
            echo "  $0 intraday   # Apply intraday preset"
            echo "  $0 custom     # Configure manually"
            ;;
        *)
            apply_preset "$preset"
            ;;
    esac
}

# Run main function with all arguments
main "$@"
