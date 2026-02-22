# ML Service Deployment Guide

## Overview

This document provides detailed guidance for deploying the ML Service as a separate microservice.

## Architecture Benefits

### Why Separate the ML Service?

1. **Independent Scaling**
   - Scale ML inference independently from API traffic
   - Add GPU instances only for ML workload
   - Cost-effective resource allocation

2. **Technology Isolation**
   - Different Python versions if needed
   - Heavy ML dependencies don't affect main backend
   - Easier to update ML models without backend deployment

3. **Performance**
   - Dedicated resources for inference
   - No resource contention with API requests
   - Better throughput for batch predictions

4. **Development Velocity**
   - Data scientists can update models independently
   - Faster iteration on ML improvements
   - A/B testing of different models

## Deployment Options

### Option 1: Docker (Recommended for Production)

**Build Image:**
```bash
cd ml-service
docker build -t mhealth-ml-service:v1.0 .
```

**Run Container:**
```bash
docker run -d \
  --name mhealth-ml-service \
  -p 8001:8001 \
  -v $(pwd)/model_store:/app/model_store \
  -e ML_SERVICE_HOST=0.0.0.0 \
  -e ML_SERVICE_PORT=8001 \
  --restart unless-stopped \
  mhealth-ml-service:v1.0
```

**Health Check:**
```bash
curl http://localhost:8001/health
```

### Option 2: Docker Compose (With Backend)

Add to backend's `docker-compose.yml`:
```yaml
ml-service:
  build:
    context: ../ml-service
  ports:
    - "8001:8001"
  volumes:
    - ../ml-service/model_store:/app/model_store
  environment:
    - ML_SERVICE_HOST=0.0.0.0
    - ML_SERVICE_PORT=8001
  networks:
    - mhealth-network
```

Start all services:
```bash
cd backend
docker-compose up -d
```

### Option 3: Kubernetes

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-service
  namespace: mhealth
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-service
  template:
    metadata:
      labels:
        app: ml-service
    spec:
      containers:
      - name: ml-service
        image: mhealth-ml-service:v1.0
        ports:
        - containerPort: 8001
        env:
        - name: ML_SERVICE_HOST
          value: "0.0.0.0"
        - name: ML_SERVICE_PORT
          value: "8001"
        volumeMounts:
        - name: model-storage
          mountPath: /app/model_store
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: ml-models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: ml-service
  namespace: mhealth
spec:
  selector:
    app: ml-service
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: ClusterIP
```

**Apply:**
```bash
kubectl apply -f k8s/ml-service.yaml
```

### Option 4: Cloud Platforms

#### AWS ECS/Fargate

1. Build and push to ECR:
```bash
aws ecr create-repository --repository-name mhealth-ml-service
docker tag mhealth-ml-service:v1.0 <account-id>.dkr.ecr.us-east-1.amazonaws.com/mhealth-ml-service:v1.0
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/mhealth-ml-service:v1.0
```

2. Create ECS task definition with model from S3
3. Deploy service with ALB for load balancing

#### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/<project-id>/ml-service
gcloud run deploy ml-service \
  --image gcr.io/<project-id>/ml-service \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10
```

#### Azure Container Instances

```bash
az container create \
  --resource-group mhealth-rg \
  --name ml-service \
  --image mhealth-ml-service:v1.0 \
  --cpu 2 \
  --memory 4 \
  --port 8001 \
  --environment-variables ML_SERVICE_PORT=8001
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ML_SERVICE_HOST` | Host to bind to | `0.0.0.0` | No |
| `ML_SERVICE_PORT` | Port to listen on | `8001` | No |
| `SENTIMENT_MODEL_PATH` | Path to model file | `./model_store/best_model.pt` | Yes |
| `TARGET_SAMPLE_RATE` | Audio sample rate | `16000` | No |
| `MAX_AUDIO_DURATION` | Max audio duration (s) | `5.27` | No |

### Backend Configuration

Update backend `.env`:
```env
# ML Service URL (adjust based on deployment)
ML_SERVICE_URL=http://ml-service:8001  # Docker Compose
# ML_SERVICE_URL=http://ml-service.mhealth.svc.cluster.local:8001  # Kubernetes
# ML_SERVICE_URL=https://ml-service-xyz.run.app  # Cloud Run
ML_SERVICE_TIMEOUT=30
```

## Model Management

### Updating Models

1. **Build new image with updated model:**
```bash
# Copy new model
cp new_best_model.pt ml-service/model_store/best_model.pt

# Rebuild image
docker build -t mhealth-ml-service:v1.1 ml-service/

# Tag for deployment
docker tag mhealth-ml-service:v1.1 mhealth-ml-service:latest
```

2. **Rolling update (Kubernetes):**
```bash
kubectl set image deployment/ml-service \
  ml-service=mhealth-ml-service:v1.1 \
  --record
  
kubectl rollout status deployment/ml-service
```

3. **Zero-downtime update:**
   - Deploy new version alongside old
   - Gradually shift traffic
   - Monitor performance
   - Complete rollover or rollback

### Model Versioning Strategy

- Tag images with model version: `ml-service:model-v1.0`
- Store models in S3/GCS with versioning enabled
- Use volume mounts for development
- Use init containers to download models in production

## Monitoring

### Health Checks

**Liveness Probe:**
```bash
curl http://ml-service:8001/health
```

**Readiness Probe:**
Test inference with dummy audio

**Metrics to Monitor:**
- Request latency (p50, p95, p99)
- Throughput (requests/sec)
- Error rate
- Model inference time
- CPU/Memory utilization
- GPU utilization (if using GPU)

### Logging

ML service logs include:
- Request IDs for tracing
- Inference timing breakdown
- Model versions
- Error stack traces

Configure log aggregation:
- CloudWatch (AWS)
- Stackdriver (GCP)
- Application Insights (Azure)
- ELK Stack (self-hosted)

## Performance Optimization

### CPU Optimization
```env
TORCH_NUM_THREADS=4
OMP_NUM_THREADS=4
```

### GPU Acceleration
```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
# ... rest of Dockerfile
```

Update deployment:
```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

### Batch Processing
Implement batch inference endpoint for multiple files:
```python
@app.post("/api/ml/sentiment/batch")
async def predict_sentiment_batch(files: List[UploadFile]):
    # Process multiple files in single batch
    pass
```

### Caching
Add Redis for caching predictions:
```python
# Cache key based on audio hash
cache_key = hashlib.md5(audio_bytes).hexdigest()
if cached := await redis.get(cache_key):
    return json.loads(cached)
```

## Security

### Authentication
Add API key authentication:
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/api/ml/sentiment")
async def predict(file: UploadFile, api_key: str = Depends(api_key_header)):
    if api_key != os.getenv("ML_API_KEY"):
        raise HTTPException(401, "Invalid API key")
    # ... rest of endpoint
```

### Network Security
- Use internal network for backend-to-ML communication
- Don't expose ML service publicly
- Use TLS for inter-service communication
- Implement rate limiting

## Cost Optimization

### Scaling Strategies

**Auto-scaling based on load:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-service
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Spot/Preemptible Instances:**
- Use for non-critical workloads
- Implement graceful degradation
- Fall back to on-demand if needed

**Scheduled Scaling:**
- Scale up during business hours
- Scale down at night
- Weekend vs weekday patterns

## Troubleshooting

See main README and ML Service README for detailed troubleshooting guides.

## Summary

The ML service provides a flexible, scalable architecture for emotion and sentiment analysis. Choose the deployment option that best fits your infrastructure and scale requirements.
