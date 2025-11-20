# Script om tests te runnen voor het AI Chat project (Windows PowerShell)

param(
    [string]$TestType = "all",
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$RemainingArgs
)

Write-Host "==================================="
Write-Host "AI Chat Project - Test Runner"
Write-Host "==================================="
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "⚠️  Geen virtual environment gevonden." -ForegroundColor Yellow
    Write-Host "   Maak er een aan met: python -m venv .venv"
    Write-Host "   Activeer met: .venv\Scripts\activate"
    exit 1
}

# Check if dependencies are installed
try {
    python -c "import pytest" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "pytest not found"
    }
} catch {
    Write-Host "📦 Installeren van test dependencies..." -ForegroundColor Cyan
    pip install -r requirements-dev.txt
}

# Set required environment variables
if (-not $env:SEARCH_ENDPOINT) {
    $env:SEARCH_ENDPOINT = "https://test.search.windows.net"
}

Write-Host "🧪 Runnen van tests..." -ForegroundColor Cyan
Write-Host ""

# Run tests based on argument
switch ($TestType) {
    "unit" {
        Write-Host "▶️  Running unit tests only..." -ForegroundColor Green
        python -m pytest tests/ -v -m "unit and not live" $RemainingArgs
    }
    "fast" {
        Write-Host "▶️  Running tests (excluding slow and live tests)..." -ForegroundColor Green
        python -m pytest tests/ -v -m "not slow and not live" $RemainingArgs
    }
    "all" {
        Write-Host "▶️  Running all tests (excluding live tests)..." -ForegroundColor Green
        python -m pytest tests/ -v -m "not live" $RemainingArgs
    }
    "live" {
        Write-Host "▶️  Running ALL tests (including live tests)..." -ForegroundColor Green
        Write-Host "⚠️  Dit vereist geldige Azure credentials!" -ForegroundColor Yellow
        python -m pytest tests/ -v $RemainingArgs
    }
    "coverage" {
        Write-Host "▶️  Running tests with coverage report..." -ForegroundColor Green
        python -m pytest tests/ -v -m "not live" --cov-report=html $RemainingArgs
        Write-Host ""
        Write-Host "📊 Coverage rapport gegenereerd in: htmlcov\index.html" -ForegroundColor Cyan
    }
    default {
        python -m pytest tests/ -v $TestType $RemainingArgs
    }
}

Write-Host ""
Write-Host "✅ Tests voltooid!" -ForegroundColor Green
