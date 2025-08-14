#!/usr/bin/env python3
"""
Configuration Manager for Enhanced Market Data Archiver

This script allows you to easily configure archiving intervals and periods.
"""

import argparse
import os
import sys

# Configuration templates
INTERVAL_OPTIONS = {
    'intraday': {
        '1m': '1 minute',
        '5m': '5 minutes', 
        '15m': '15 minutes',
        '30m': '30 minutes',
        '1h': '1 hour'
    },
    'daily': {
        '1d': '1 day',
        '5d': '5 days'
    },
    'weekly': {
        '1wk': '1 week'
    },
    'monthly': {
        '1mo': '1 month',
        '3mo': '3 months'
    }
}

PERIOD_OPTIONS = {
    'short': {
        '1d': '1 day',
        '5d': '5 days',
        '7d': '1 week'
    },
    'medium': {
        '1mo': '1 month',
        '3mo': '3 months',
        '6mo': '6 months'
    },
    'long': {
        '1y': '1 year',
        '2y': '2 years',
        '5y': '5 years',
        'max': 'Maximum available'
    }
}

MONITORING_INTERVALS = {
    '300': '5 minutes',
    '600': '10 minutes', 
    '1800': '30 minutes',
    '3600': '1 hour',
    '7200': '2 hours',
    '14400': '4 hours',
    '21600': '6 hours',
    '43200': '12 hours',
    '86400': '24 hours'
}

def display_options():
    """Display all available configuration options."""
    print("📊 Enhanced Market Data Archiver - Configuration Options")
    print("=" * 60)
    
    print("\n🕐 Data Intervals (YFinance):")
    for category, intervals in INTERVAL_OPTIONS.items():
        print(f"  {category.title()}:")
        for code, desc in intervals.items():
            print(f"    {code:4} - {desc}")
    
    print("\n📅 Data Periods (Historical Range):")
    for category, periods in PERIOD_OPTIONS.items():
        print(f"  {category.title()}:")
        for code, desc in periods.items():
            print(f"    {code:4} - {desc}")
    
    print("\n⏰ Monitoring Intervals (Continuous Mode):")
    for seconds, desc in MONITORING_INTERVALS.items():
        print(f"    {seconds:5}s - {desc}")

def update_archiver_config(interval='1d', period='30d'):
    """Update the enhanced archiver configuration."""
    archiver_path = '/app/enhanced_archiver.py'
    
    try:
        # Read current file
        with open(archiver_path, 'r') as f:
            content = f.read()
        
        # Find and replace the configuration line
        old_line = None
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if 'archive_all_symbols(interval=' in line and 'period=' in line:
                old_line = line
                new_line = f"    results = archiver.archive_all_symbols(interval='{interval}', period='{period}', delay=0.5)"
                lines[i] = new_line
                break
        
        if old_line:
            # Write updated file
            with open(archiver_path, 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ Updated archiver configuration:")
            print(f"   Interval: {interval}")
            print(f"   Period: {period}")
            print(f"   File: {archiver_path}")
        else:
            print("❌ Could not find configuration line to update")
            
    except FileNotFoundError:
        print(f"❌ Archiver file not found: {archiver_path}")
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")

def update_monitoring_interval(seconds=3600):
    """Update the monitoring script interval."""
    script_path = '/app/../scripts/enhanced-archiver.sh'
    
    try:
        # Read current file
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Calculate human-readable time
        if seconds >= 3600:
            time_desc = f"{seconds // 3600} hour{'s' if seconds // 3600 > 1 else ''}"
        elif seconds >= 60:
            time_desc = f"{seconds // 60} minute{'s' if seconds // 60 > 1 else ''}"
        else:
            time_desc = f"{seconds} second{'s' if seconds > 1 else ''}"
        
        # Replace monitoring interval
        content = content.replace(
            'sleep 3600  # 1 hour (3600 seconds)',
            f'sleep {seconds}  # {time_desc} ({seconds} seconds)'
        )
        
        content = content.replace(
            'echo "⏰ Next enhanced archival in 1 hour..."',
            f'echo "⏰ Next enhanced archival in {time_desc}..."'
        )
        
        content = content.replace(
            'echo "  monitor          Run continuous enhanced archival every 1 hour"',
            f'echo "  monitor          Run continuous enhanced archival every {time_desc}"'
        )
        
        # Write updated file
        with open(script_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated monitoring interval to {time_desc}")
        print(f"   File: {script_path}")
        
    except FileNotFoundError:
        print(f"❌ Script file not found: {script_path}")
    except Exception as e:
        print(f"❌ Error updating monitoring interval: {e}")

def main():
    """Main configuration function."""
    parser = argparse.ArgumentParser(
        description='Configure Enhanced Market Data Archiver intervals'
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all available configuration options')
    
    parser.add_argument('--interval', type=str, default='1d',
                       help='Data interval (default: 1d)')
    
    parser.add_argument('--period', type=str, default='30d',
                       help='Data period (default: 30d)')
    
    parser.add_argument('--monitor', type=int, default=3600,
                       help='Monitoring interval in seconds (default: 3600 = 1 hour)')
    
    parser.add_argument('--preset', type=str, choices=['intraday', 'daily', 'weekly', 'monthly'],
                       help='Use a preset configuration')
    
    args = parser.parse_args()
    
    if args.list:
        display_options()
        return
    
    # Apply preset configurations
    if args.preset:
        presets = {
            'intraday': {'interval': '5m', 'period': '1d', 'monitor': 300},  # 5min data, 5min monitoring
            'daily': {'interval': '1d', 'period': '30d', 'monitor': 3600},   # Daily data, hourly monitoring
            'weekly': {'interval': '1wk', 'period': '6mo', 'monitor': 86400}, # Weekly data, daily monitoring
            'monthly': {'interval': '1mo', 'period': '2y', 'monitor': 86400}  # Monthly data, daily monitoring
        }
        
        preset_config = presets[args.preset]
        args.interval = preset_config['interval']
        args.period = preset_config['period']
        args.monitor = preset_config['monitor']
        
        print(f"🎯 Applying {args.preset} preset:")
        print(f"   Interval: {args.interval}")
        print(f"   Period: {args.period}")
        print(f"   Monitoring: {args.monitor}s")
        print()
    
    # Update configurations
    update_archiver_config(args.interval, args.period)
    update_monitoring_interval(args.monitor)
    
    print("\n🎉 Configuration updated successfully!")
    print("\n📋 To apply changes:")
    print("   1. Restart your services if running")
    print("   2. Run: ./scripts/enhanced-archiver.sh enhanced-archive")
    print("   3. For continuous monitoring: ./scripts/enhanced-archiver.sh monitor")

if __name__ == "__main__":
    main()
