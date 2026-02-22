# Migration Guide: Monolith to Microservices ML

This guide helps you migrate from the embedded ML service to the separate ML microservice architecture.

## Overview of Changes

### Before (Monolithic)
```
Backend
├── ML Models (PyTorch, sklearn)
├── ML Inference Code
├── API Routes
└── Business Logic
```

### After (Microservices)
```
Backend                          ML Service
├── API Routes                   ├── ML Models
├── Business Logic               ├── Inference Code
├── ML Client (HTTP)             └── REST API
└── Database Logic
```

## Migration Steps

### Step 1: Prepare ML Service

1. **Copy model files:**
```bash
# Create ML service directory structure
mkdir -p ml-service/model_store

# Copy model from backend to ML service
cp backend/model_store/best_model.pt ml-service/model_store/
```

2. **Set up ML service environment:**
```bash
cd ml-service
cp .env.example .env
# Edit .env if needed
```

3. **Test ML service locally:**
```bash
cd ml-service
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8001
```

4. **Verify ML service is working:**
```bash
# In another terminal
curl http://localhost:8001/health

# Should return:
# {"status":"healthy","service":"ml-service","version":"1.0.0","models_loaded":{...}}
```

### Step 2: Update Backend Configuration

1. **Update backend .env:**
```bash
cd backend
# Add to .env:
echo "ML_SERVICE_URL=http://localhost:8001" >> .env
echo "ML_SERVICE_TIMEOUT=30" >> .env
```

2. **Update requirements.txt:**
The heavy ML dependencies are now removed from backend:
```
# These are now only in ml-service:
# torch          (removed)
# torchaudio     (removed)
# transformers   (removed)
```

3. **Reinstall backend dependencies:**
```bash
cd backend
pip install -r requirements.txt --upgrade
```

### Step 3: Update Backend Code

The migration is already complete in the codebase. Key changes:

1. **New file: `backend/app/ml_client.py`**
   - HTTP client for ML service
   - Synchronous wrappers for Celery

2. **Updated: `backend/app/api/ml_routes.py`**
   - Now proxies requests to ML service
   - No longer loads models locally

3. **Updated: `backend/app/celery_config_exotel.py`**
   - Uses `predict_sentiment_sync()` from ml_client
   - No longer uses EmotionModelService locally

4. **Updated: `backend/app/config.py`**
   - Added ML_SERVICE_URL
   - Added ML_SERVICE_TIMEOUT

### Step 4: Test Integration

1. **Start ML service:**
```bash
cd ml-service
python -m uvicorn app.main:app --port 8001
```

2. **Start backend:**
```bash
cd backend
uvicorn app.main_exotel:app --port 8000
```

3. **Test sentiment endpoint through backend:**
```bash
curl -X POST "http://localhost:8000/api/ml/sentiment" \
  -F "file=@test_audio.mp3"
```

4. **Verify Celery integration:**
```bash
# Start Celery worker
celery -A app.celery_config_exotel worker --loglevel=info

# Trigger a test call that will process recording
# Check logs to see ML service being called
```

### Step 5: Deploy with Docker Compose

1. **Update docker-compose.yml:**

The updated `backend/docker-compose.yml` now includes:
```yaml
ml-service:
  build:
    context: ../ml-service
  ports:
    - "8001:8001"
  volumes:
    - ../ml-service/model_store:/app/model_store
```

2. **Start all services:**
```bash
cd backend
docker-compose up -d
```

3. **Verify all containers:**
```bash
docker-compose ps

# Should show:
# - mhealth-postgres
# - mhealth-rabbitmq
# - mhealth-minio
# - mhealth-ml-service  (NEW!)
```

### Step 6: Production Deployment

Choose your deployment strategy:

**Option A: Same Host**
- ML service runs on same server as backend
- `ML_SERVICE_URL=http://localhost:8001`
- Good for small deployments

**Option B: Separate Host**
- ML service on dedicated server/VM
- `ML_SERVICE_URL=http://ml-server.internal:8001`
- Better for scaling

**Option C: Kubernetes**
- ML service as separate deployment
- `ML_SERVICE_URL=http://ml-service.mhealth.svc.cluster.local:8001`
- Best for large scale

**Option D: Cloud Platform**
- ML service on Cloud Run/ECS/Container Instances
- `ML_SERVICE_URL=https://ml-service-xyz.run.app`
- Serverless scaling

## Rollback Plan

If you need to rollback to the monolithic architecture:

1. **Keep old code in git:**
```bash
git checkout <commit-before-migration>
```

2. **Or disable ML service:**
```python
# In backend/app/config.py
ML_SERVICE_URL = None  # Will use local models

# Keep old vad_sentiment.py in backend/app/services/
```

3. **Restore heavy dependencies:**
```bash
# Add back to requirements.txt:
torch
torchaudio
transformers
```

## Verification Checklist

- [ ] ML service starts successfully
- [ ] ML service health endpoint responds
- [ ] Backend can connect to ML service
- [ ] Sentiment analysis through backend works
- [ ] Celery emotion processing works
- [ ] Docker compose includes ML service
- [ ] All tests pass
- [ ] Performance is acceptable
- [ ] Logs show successful ML service calls
- [ ] Error handling works (ML service down)

## Performance Comparison

### Before (Monolithic)
- Backend memory: ~3-4 GB (with models loaded)
- Startup time: 30-60 seconds (model loading)
- Scaling: All or nothing

### After (Microservices)
- Backend memory: ~500 MB - 1 GB
- ML service memory: ~2-3 GB
- Backend startup: 5-10 seconds
- ML service startup: 30-60 seconds
- Scaling: Independent

## Common Migration Issues

### Issue 1: ML Service Connection Refused
**Symptom:** Backend logs show connection errors to ML service

**Solution:**
```bash
# Verify ML service is running
curl http://localhost:8001/health

# Check backend config
echo $ML_SERVICE_URL

# Update backend .env
ML_SERVICE_URL=http://localhost:8001  # or correct URL
```

### Issue 2: Model Not Found
**Symptom:** ML service fails to start, model file not found

**Solution:**
```bash
# Ensure model file exists
ls -lh ml-service/model_store/best_model.pt

# Check Dockerfile COPY command
# Verify volume mounts in docker-compose.yml
```

### Issue 3: Timeout Errors
**Symptom:** Backend times out waiting for ML service

**Solution:**
```bash
# Increase timeout in backend .env
ML_SERVICE_TIMEOUT=60  # seconds

# Or optimize ML service:
# - Use GPU
# - Reduce model size
# - Process smaller audio chunks
```

### Issue 4: Celery Can't Reach ML Service
**Symptom:** Emotion processing fails in Celery tasks

**Solution:**
```bash
# Celery workers need network access to ML service
# Update ML_SERVICE_URL to use Docker network:
ML_SERVICE_URL=http://ml-service:8001  # Docker network name

# Or use host network mode
# Or ensure proper DNS resolution
```

## Benefits Realized

After migration, you should see:

✅ **Better Resource Utilization**
- Backend uses less memory
- Can run more backend instances

✅ **Independent Scaling**
- Scale ML service based on inference load
- Scale backend based on API traffic

✅ **Faster Deployments**
- Update ML models without backend restart
- Update backend without ML service impact

✅ **Better Development**
- Data scientists work independently
- Clearer separation of concerns
- Easier testing

✅ **Cost Optimization**
- Right-size each service
- Use GPU only where needed
- Scale down during off-hours

## Next Steps

1. **Monitor Performance:**
   - Set up metrics collection
   - Track latency and throughput
   - Monitor resource usage

2. **Optimize ML Service:**
   - Add caching for common requests
   - Implement batch processing
   - Consider GPU acceleration

3. **Add Observability:**
   - Distributed tracing
   - Log aggregation
   - Error tracking

4. **Implement Auto-scaling:**
   - Based on queue depth
   - Based on CPU/memory
   - Scheduled scaling

## Support

For issues during migration:
1. Check logs: `docker-compose logs -f ml-service`
2. Review troubleshooting section in main README
3. Verify each step in this guide

## Summary

The migration separates ML inference into a dedicated microservice, enabling better scaling, resource utilization, and development velocity. Follow the steps carefully and verify each stage before proceeding.
