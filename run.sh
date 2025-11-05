#!/bin/bash
# Quick launch script for V-Li Switch Manager
# This script handles first-time setup and launches the application

set -e  # Exit on error

echo "🚀 V-Li Switch Manager Launcher"
echo ""

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.11 or higher from https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or higher is required"
    echo "Please upgrade Python from https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import textual" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed"
fi

# Set environment variables (can be overridden)
export SM_USER="${SM_USER:-$(whoami)}"
export SM_CSV_DATA="${SM_CSV_DATA:-data.csv}"
export SM_DELIMITER="${SM_DELIMITER:-;}"
export SM_TMUX_MODE="${SM_TMUX_MODE:-attach}"

echo ""
echo "⚙️  Configuration:"
echo "   SM_USER: $SM_USER"
echo "   SM_CSV_DATA: $SM_CSV_DATA"
echo "   SM_TMUX_MODE: $SM_TMUX_MODE"
echo ""

# Check if data file exists
if [ ! -f "$SM_CSV_DATA" ]; then
    echo "⚠️  Warning: CSV file '$SM_CSV_DATA' not found"
    echo "   The app will still launch, but no switches will be loaded."
    echo ""
fi

echo "🎯 Launching V-Li Switch Manager..."
echo ""

# Run the application
python -m switch_manager
