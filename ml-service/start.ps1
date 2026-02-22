# Quick Start Script for ML Service (Windows)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Mental Health ML Service - Quick Start" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists, create if not
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created in .\venv\" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Check if model file exists
if (-Not (Test-Path "model_store\best_model.pt")) {
    Write-Host "WARNING: Model file not found!" -ForegroundColor Yellow
    Write-Host "Please place best_model.pt in model_store\ directory" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  1. Copy from backend: cp ..\backend\model_store\best_model.pt .\model_store\" -ForegroundColor White
    Write-Host "  2. Download your trained model to .\model_store\best_model.pt" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue without model? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created" -ForegroundColor Green
}

# Install/upgrade dependencies
Write-Host "Installing dependencies to virtual environment..." -ForegroundColor Green
Write-Host "Location: $(Get-Location)\venv\Lib\site-packages" -ForegroundColor Cyan
pip install -r requirements.txt

# Start the service
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starting ML Service on http://localhost:8001..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
