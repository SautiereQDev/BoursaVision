#!/bin/bash

# Python Version Compatibility Check for Boursa Vision
# ====================================================

set -e

echo "🔍 Checking Python version compatibility..."

# Get current Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Current Python version: $PYTHON_VERSION"

# Check if Python version is compatible
case $PYTHON_VERSION in
    "3.11"|"3.12")
        echo "✅ Python $PYTHON_VERSION is compatible"
        ;;
    "3.13")
        echo "⚠️  Python 3.13 detected - some packages may have compatibility issues"
        echo "🔧 Using Docker with Python 3.11 is recommended for development"
        
        # Check if we're in Docker
        if [ -f /.dockerenv ]; then
            echo "📦 Running in Docker container - should be fine"
        else
            echo "💡 Consider using 'make dev' to run with Docker instead"
        fi
        ;;
    *)
        echo "❌ Python $PYTHON_VERSION may not be fully compatible"
        echo "🎯 Recommended: Python 3.11 or 3.12"
        echo "🐳 Use Docker for consistent environment: make dev"
        ;;
esac

# Check for specific package compatibility issues
echo ""
echo "🔍 Checking package compatibility..."

# Check if asyncpg can be installed
if python3 -c "import asyncpg" 2>/dev/null; then
    echo "✅ asyncpg is available and working"
else
    echo "⚠️  asyncpg may need compilation or is not compatible"
    echo "🔧 Suggestions:"
    echo "   - Use Docker: make dev"
    echo "   - Install build dependencies: sudo apt install build-essential libpq-dev"
    echo "   - Use Python 3.11 or 3.12"
fi

echo ""
echo "🚀 For best compatibility, use: make dev"
