# Quick SSL Setup Script - Self-Signed Certificate (PowerShell)
# For testing/development use
# Run this on Windows to generate and upload certificates to server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "mHealth SSL Setup - Self-Signed Certificate" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SERVER = "10.0.62.206"
$PORT = "2022"
$USER = "shivansh.gupta"
$REMOTE_PATH = "/home/shivansh.gupta/mhealth/backend/ssl"

# Create local SSL directory
Write-Host "Creating local SSL directory..." -ForegroundColor Cyan
$sslDir = Join-Path $PSScriptRoot "backend\ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir | Out-Null
}

# Check if OpenSSL is available
try {
    $null = openssl version 2>&1
} catch {
    Write-Host "❌ OpenSSL not found!" -ForegroundColor Red
    Write-Host "Please install OpenSSL:" -ForegroundColor Yellow
    Write-Host "  - Download: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Yellow
    Write-Host "  - Or install via: winget install OpenSSL.Light" -ForegroundColor Yellow
    exit 1
}

# Generate self-signed certificate
Write-Host ""
Write-Host "Generating self-signed SSL certificate..." -ForegroundColor Cyan
Write-Host "(Valid for 1 year)" -ForegroundColor Gray

$certPath = Join-Path $sslDir "cert.pem"
$keyPath = Join-Path $sslDir "key.pem"

# Check if certificate already exists
if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    Write-Host "⚠️  SSL certificates already exist locally!" -ForegroundColor Yellow
    $response = Read-Host "Do you want to replace them? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "Keeping existing certificates." -ForegroundColor Yellow
        exit 0
    }
}

# Generate certificate
$subject = "/C=IN/ST=Gujarat/L=Gandhinagar/O=IIT Gandhinagar/OU=mHealth/CN=mhealth.iitgn.ac.in"

try {
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
        -keyout $keyPath `
        -out $certPath `
        -subj $subject 2>&1 | Out-Null
    
    Write-Host "✅ Certificate generated successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to generate certificate" -ForegroundColor Red
    exit 1
}

# Show certificate details
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Certificate Details:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
openssl x509 -in $certPath -noout -subject -issuer -dates

# Upload to server
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading to Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Create remote SSL directory
Write-Host "Creating remote SSL directory..." -ForegroundColor Cyan
ssh -p $PORT "${USER}@${SERVER}" "mkdir -p ${REMOTE_PATH}"

# Upload certificate files
Write-Host "Uploading certificate..." -ForegroundColor Cyan
scp -P $PORT $certPath "${USER}@${SERVER}:${REMOTE_PATH}/cert.pem"

Write-Host "Uploading private key..." -ForegroundColor Cyan
scp -P $PORT $keyPath "${USER}@${SERVER}:${REMOTE_PATH}/key.pem"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Files uploaded successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to upload files" -ForegroundColor Red
    exit 1
}

# Set permissions on server
Write-Host "Setting file permissions on server..." -ForegroundColor Cyan
ssh -p $PORT "${USER}@${SERVER}" "chmod 600 ${REMOTE_PATH}/key.pem && chmod 644 ${REMOTE_PATH}/cert.pem"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Update .env file on server:" -ForegroundColor Yellow
Write-Host "   FRONTEND_URL=https://mhealth.iitgn.ac.in,https://10.0.62.206" -ForegroundColor White
Write-Host ""
Write-Host "2. Restart Docker services on server:" -ForegroundColor Yellow
Write-Host "   ssh -p $PORT ${USER}@${SERVER}" -ForegroundColor White
Write-Host "   cd /home/shivansh.gupta/mhealth" -ForegroundColor White
Write-Host "   docker compose down" -ForegroundColor White
Write-Host "   docker compose up -d --build" -ForegroundColor White
Write-Host ""
Write-Host "3. Access your application:" -ForegroundColor Yellow
Write-Host "   https://mhealth.iitgn.ac.in" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  Note: Browsers will show a security warning for self-signed certificates." -ForegroundColor Yellow
Write-Host "   This is normal. Click 'Advanced' → 'Proceed to site' to continue." -ForegroundColor Gray
Write-Host ""
Write-Host "For production, use Let's Encrypt instead:" -ForegroundColor Cyan
Write-Host "   See SSL_SETUP_GUIDE.md for instructions" -ForegroundColor Gray
Write-Host ""
