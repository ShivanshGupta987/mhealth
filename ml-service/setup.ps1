# Setup Script for ML Service (Windows)
# This creates the virtual environment and installs dependencies

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "ML Service - Initial Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create virtual environment
Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, skipping..." -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
}
Write-Host ""

# Step 2: Activate venv
Write-Host "[2/4] Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "Dependencies will be installed to:" -ForegroundColor Cyan
Write-Host "  $(Get-Location)\venv\Lib\site-packages" -ForegroundColor White
Write-Host ""

# Step 3: Install dependencies
Write-Host "[3/4] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "This may take several minutes (PyTorch is ~2GB)..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Check model file
Write-Host "[4/4] Checking for model file..." -ForegroundColor Yellow
if (Test-Path "model_store\best_model.pt") {
    Write-Host "Model file found: model_store\best_model.pt" -ForegroundColor Green
    $size = (Get-Item "model_store\best_model.pt").Length / 1MB
    Write-Host "Model size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
} else {
    Write-Host "WARNING: Model file not found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please copy your model file to:" -ForegroundColor White
    Write-Host "  $(Get-Location)\model_store\best_model.pt" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Example:" -ForegroundColor White
    Write-Host "  cp ..\backend\model_store\best_model.pt .\model_store\" -ForegroundColor Gray
}
Write-Host ""

# Step 5: Create .env if needed
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created" -ForegroundColor Green
}

# Done
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Ensure model file is in model_store\" -ForegroundColor White
Write-Host "  2. Review/edit .env file if needed" -ForegroundColor White
Write-Host "  3. Run: .\start.ps1" -ForegroundColor White
Write-Host ""
