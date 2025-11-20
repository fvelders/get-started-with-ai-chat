#!/bin/bash
# Script om tests te runnen voor het AI Chat project

set -e

echo "==================================="
echo "AI Chat Project - Test Runner"
echo "==================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Geen virtual environment gevonden."
    echo "   Maak er een aan met: python3 -m venv .venv"
    echo "   Activeer met: source .venv/bin/activate"
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installeren van test dependencies..."
    pip install -r requirements-dev.txt
fi

# Set required environment variables
export SEARCH_ENDPOINT="${SEARCH_ENDPOINT:-https://test.search.windows.net}"

echo "🧪 Runnen van tests..."
echo ""

# Run tests based on argument
case "${1:-all}" in
    "unit")
        echo "▶️  Running unit tests only..."
        python -m pytest tests/ -v -m "unit and not live" "${@:2}"
        ;;
    "fast")
        echo "▶️  Running tests (excluding slow and live tests)..."
        python -m pytest tests/ -v -m "not slow and not live" "${@:2}"
        ;;
    "all")
        echo "▶️  Running all tests (excluding live tests)..."
        python -m pytest tests/ -v -m "not live" "${@:2}"
        ;;
    "live")
        echo "▶️  Running ALL tests (including live tests)..."
        echo "⚠️  Dit vereist geldige Azure credentials!"
        python -m pytest tests/ -v "${@:2}"
        ;;
    "coverage")
        echo "▶️  Running tests with coverage report..."
        python -m pytest tests/ -v -m "not live" --cov-report=html "${@:2}"
        echo ""
        echo "📊 Coverage rapport gegenereerd in: htmlcov/index.html"
        ;;
    *)
        python -m pytest tests/ -v "$@"
        ;;
esac

echo ""
echo "✅ Tests voltooid!"
