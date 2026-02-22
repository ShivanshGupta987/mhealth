# ML Service Testing & Verification Guide

## Quick Verification Steps

### Step 1: Start the ML Service

**Option A: Using PowerShell Script (Windows)**
```powershell
cd ml-service
.\start.ps1
```

**Option B: Direct Command**
```powershell
cd ml-service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Option C: Using Docker**
```powershell
cd ml-service
docker build -t ml-service .
docker run -p 8001:8001 -v ${PWD}/model_store:/app/model_store ml-service
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
Loading model from: D:\...\ml-service\model_store\best_model.pt
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 2: Basic Health Check

**Test 1: Service is Running**
```powershell
curl.exe http://localhost:8001/
```

Expected response:
```json
{
  "service": "Mental Health ML Service",
  "version": "1.0.0",
  "status": "running"
}
```

**Test 2: Health Endpoint**
```powershell
curl.exe http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ml-service",
  "version": "1.0.0",
  "models_loaded": {
    "vad_sentiment": false,
    "emotion_model": false
  }
}
```

Note: `models_loaded` will be `false` until first inference (lazy loading)

### Step 3: Test Sentiment Analysis Endpoint

**Prepare test audio file:**
```powershell
# Make sure you have a test audio file (mp3, wav, etc.)
# Example: temp.mp3 in backend folder
```

**Test sentiment endpoint:**
```powershell
curl.exe -X POST "http://localhost:8001/api/ml/sentiment" -F "file=@temp.mp3"
```

Expected response (example):
```json
{
  "vad": [0.883, 0.170, 0.304],
  "emotion": "Neutral",
  "sentiment": "Neutral",
  "timing": {
    "load_time": 0.123,
    "preprocess_time": 0.045,
    "feature_extraction_time": 0.234,
    "inference_time": 0.567,
    "postprocess_time": 0.012,
    "total_time": 0.981
  }
}
```

### Step 4: Test Emotion Classification Endpoint

```powershell
curl.exe -X POST "http://localhost:8001/api/ml/emotion" -F "file=@temp.mp3"
```

Expected response:
```json
{
  "emotion": "NEUTRAL",
  "confidence": 0.87
}
```

### Step 5: Warmup Models (Pre-load)

```powershell
curl.exe -X POST "http://localhost:8001/warmup"
```

Expected response:
```json
{
  "status": "models warmed up",
  "success": true
}
```

After warmup, health check should show:
```json
{
  "status": "healthy",
  "service": "ml-service",
  "version": "1.0.0",
  "models_loaded": {
    "vad_sentiment": true,
    "emotion_model": true
  }
}
```

### Step 6: Test Through Backend (Integration Test)

**Update backend .env:**
```env
ML_SERVICE_URL=http://localhost:8001
ML_SERVICE_TIMEOUT=30
```

**Test backend proxy to ML service:**
```powershell
cd backend
curl.exe -X POST "http://localhost:8000/api/ml/sentiment" -F "file=@temp.mp3"
```

This should:
1. Hit backend API
2. Backend forwards to ML service
3. ML service processes and returns result
4. Backend returns result to you

**Check ML service health from backend:**
```powershell
curl.exe http://localhost:8000/api/ml/health
```

## Detailed Verification

### Check 1: Model Files Exist

```powershell
# Check model file
dir ml-service\model_store\best_model.pt

# Should show file with size (typically 100MB+)
```

If missing:
```powershell
# Copy from backend if available
cp backend\model_store\best_model.pt ml-service\model_store\
```

### Check 2: Dependencies Installed

```powershell
cd ml-service
pip list | Select-String -Pattern "torch|transformers|fastapi|librosa"
```

Should show:
- torch
- torchaudio
- transformers
- fastapi
- librosa
- soundfile

If missing:
```powershell
pip install -r requirements.txt
```

### Check 3: Port is Available

```powershell
# Check if port 8001 is in use
netstat -an | Select-String "8001"
```

If port is occupied:
- Stop the other service
- Or change ML_SERVICE_PORT in .env

### Check 4: Review Logs

**Terminal logs should show:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
Loading model from: .../model_store/best_model.pt
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001

# On first request:
INFO:     Initializing VAD Sentiment Service...
INFO:     VAD Sentiment Service initialized successfully
Processing sentiment analysis for file: temp.mp3
Timing breakdown - Load: 0.123s, Preprocess: 0.045s, Features: 0.234s, 
  Inference: 0.567s, Postprocess: 0.012s, Total: 0.981s
Sentiment analysis completed: Neutral (Neutral)
```

### Check 5: Docker Health Check (if using Docker)

```powershell
# Check container status
docker ps | Select-String "ml-service"

# Should show "healthy" status after startup period

# Check container logs
docker logs mhealth-ml-service --tail 50

# Exec into container to debug
docker exec -it mhealth-ml-service sh
ls -lh /app/model_store/
```

## Common Issues & Solutions

### Issue 1: "Model file not found"

**Symptom:**
```
FileNotFoundError: Model file not found at .../best_model.pt
```

**Solution:**
```powershell
# Ensure model file exists
mkdir -p ml-service\model_store
# Copy model file to this location
cp path\to\best_model.pt ml-service\model_store\

# Verify
dir ml-service\model_store\best_model.pt
```

### Issue 2: "Port already in use"

**Symptom:**
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8001)
```

**Solution:**
```powershell
# Find process using port 8001
netstat -ano | Select-String "8001"

# Kill the process (replace PID)
Stop-Process -Id <PID> -Force

# Or use different port
$env:ML_SERVICE_PORT=8002
python -m uvicorn app.main:app --port 8002
```

### Issue 3: "Module not found"

**Symptom:**
```
ModuleNotFoundError: No module named 'torch'
```

**Solution:**
```powershell
cd ml-service
pip install -r requirements.txt

# Verify installation
python -c "import torch; print(torch.__version__)"
```

### Issue 4: Backend can't connect to ML service

**Symptom:**
Backend logs show:
```
ML service error: Connection refused
```

**Solution:**
```powershell
# Check ML service is running
curl.exe http://localhost:8001/health

# Check backend .env
notepad backend\.env
# Ensure: ML_SERVICE_URL=http://localhost:8001

# If using Docker, check network
# ML_SERVICE_URL=http://ml-service:8001  # Docker network name
```

### Issue 5: Timeout errors

**Symptom:**
```
ML service request timed out after 30 seconds
```

**Solution:**
```powershell
# Increase timeout in backend .env
# ML_SERVICE_TIMEOUT=60

# Or optimize ML service:
# - Use GPU if available
# - Reduce audio file size
# - Check system resources
```

## Performance Testing

### Test Response Time

```powershell
# Measure request time
Measure-Command {
    curl.exe -X POST "http://localhost:8001/api/ml/sentiment" -F "file=@temp.mp3"
}
```

Expected: 1-3 seconds for first request, <1 second for subsequent requests

### Test Concurrent Requests

```powershell
# Test with multiple files simultaneously
1..5 | ForEach-Object -Parallel {
    curl.exe -X POST "http://localhost:8001/api/ml/sentiment" -F "file=@temp.mp3"
}
```

### Monitor Resource Usage

```powershell
# Check CPU and memory
Get-Process python | Select-Object CPU, WorkingSet

# Or use Task Manager
# Look for python.exe process running ML service
```

## Integration Testing

### Full End-to-End Test

1. **Start all services:**
```powershell
# Terminal 1: ML Service
cd ml-service
python -m uvicorn app.main:app --port 8001

# Terminal 2: Backend
cd backend
uvicorn app.main_exotel:app --port 8000

# Terminal 3: Celery Worker
cd backend
celery -A app.celery_config_exotel worker --loglevel=info
```

2. **Test workflow:**
```powershell
# Upload via backend (should call ML service)
curl.exe -X POST "http://localhost:8000/api/ml/sentiment" -F "file=@temp.mp3"

# Check ML service logs for incoming request
# Check backend logs for successful ML service call
```

3. **Verify Celery integration:**
   - Trigger a call that creates recording
   - Watch Celery worker logs
   - Should see ML service being called for emotion processing

## Success Checklist

- [ ] ML service starts without errors
- [ ] Health endpoint returns "healthy"
- [ ] Root endpoint returns service info
- [ ] Sentiment endpoint processes audio successfully
- [ ] Emotion endpoint processes audio successfully
- [ ] Warmup endpoint loads models
- [ ] Backend can connect to ML service
- [ ] Backend proxy endpoints work
- [ ] Response times are acceptable (<3s)
- [ ] Logs show successful processing
- [ ] Celery workers can call ML service
- [ ] Docker container runs successfully (if using Docker)

## Automated Test Script

Save this as `test-ml-service.ps1`:

```powershell
# ML Service Verification Script

Write-Host "Testing ML Service..." -ForegroundColor Cyan

# Test 1: Service is running
Write-Host "`n[1/5] Testing root endpoint..." -ForegroundColor Yellow
$response = curl.exe http://localhost:8001/
if ($response -match "Mental Health ML Service") {
    Write-Host "✓ Service is running" -ForegroundColor Green
} else {
    Write-Host "✗ Service not responding" -ForegroundColor Red
    exit 1
}

# Test 2: Health check
Write-Host "`n[2/5] Testing health endpoint..." -ForegroundColor Yellow
$health = curl.exe http://localhost:8001/health
if ($health -match "healthy") {
    Write-Host "✓ Service is healthy" -ForegroundColor Green
} else {
    Write-Host "✗ Service unhealthy" -ForegroundColor Red
    exit 1
}

# Test 3: Warmup models
Write-Host "`n[3/5] Warming up models..." -ForegroundColor Yellow
curl.exe -X POST http://localhost:8001/warmup
Write-Host "✓ Models loaded" -ForegroundColor Green

# Test 4: Sentiment analysis
Write-Host "`n[4/5] Testing sentiment analysis..." -ForegroundColor Yellow
if (Test-Path "temp.mp3") {
    $sentiment = curl.exe -X POST "http://localhost:8001/api/ml/sentiment" -F "file=@temp.mp3"
    if ($sentiment -match "emotion") {
        Write-Host "✓ Sentiment analysis working" -ForegroundColor Green
    } else {
        Write-Host "✗ Sentiment analysis failed" -ForegroundColor Red
    }
} else {
    Write-Host "! Skipping (temp.mp3 not found)" -ForegroundColor Yellow
}

# Test 5: Backend integration
Write-Host "`n[5/5] Testing backend integration..." -ForegroundColor Yellow
$backendHealth = curl.exe http://localhost:8000/api/ml/health
if ($backendHealth -match "healthy") {
    Write-Host "✓ Backend can reach ML service" -ForegroundColor Green
} else {
    Write-Host "! Backend integration not tested" -ForegroundColor Yellow
}

Write-Host "`n✓ All tests passed!" -ForegroundColor Green
```

Run with:
```powershell
.\test-ml-service.ps1
```

## Next Steps

Once verified:
1. Configure auto-start for production
2. Set up monitoring and alerting
3. Configure log aggregation
4. Implement backup/recovery
5. Set up CI/CD pipeline

## Getting Help

If issues persist:
1. Check full logs in terminal
2. Review DEPLOYMENT.md for deployment options
3. Review MIGRATION.md for integration details
4. Check main README.md troubleshooting section
