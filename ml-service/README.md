# ML Service

A standalone microservice for depression risk prediction from audio recordings.

## Features

- **Depression Risk Prediction**: Random Forest model with TSFEL feature extraction from audio
- **Batch Prediction**: Analyze multiple audio files in one request
- **RESTful API**: FastAPI-based endpoints
- **Docker Support**: Containerized deployment
- **Health Monitoring**: Built-in health check endpoints

## API Endpoints

### Depression Prediction
```
POST /api/ml/depression
- Upload a single audio file
- Returns: risk (0/1), risk_level, risk_probability, risk_confidence, segment_count
```

### Batch Depression Prediction
```
POST /api/ml/depression-batch
- Upload multiple audio files
- Returns: list of per-file prediction results
```

### Health Check
```
GET /health
- Returns service status and model loading state
```

### Model Warmup
```
POST /warmup
- Pre-loads the model into memory
```

## Quick Start

### Local Development

1. **Install dependencies:**
```bash
cd ml-service
pip install -r requirements.txt
```

2. **Copy model file:**
Ensure `random_forest_model.pkl` is in the `model_store/` directory.

3. **Run the service:**
```bash
uvicorn app.main:app --reload --port 8001
```

### Docker Deployment

```bash
docker build -t mhealth-ml-service .
docker run -p 8001:8001 \
  -v $(pwd)/model_store:/app/model_store \
  mhealth-ml-service
```

### Using Docker Compose

From the project root:
```bash
docker compose up ml-service
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ML_SERVICE_HOST` | `0.0.0.0` | Host to bind to |
| `ML_SERVICE_PORT` | `8001` | Port to listen on |
| `DEPRESSION_MODEL_PATH` | `./model_store/random_forest_model.pkl` | Path to model file |
| `TARGET_SAMPLE_RATE` | `16000` | Audio sample rate (Hz) |
| `SEGMENT_DURATION` | `7` | Segment length for feature extraction (seconds) |
| `MIN_RECORDING_DURATION_SECONDS` | `3` | Minimum audio duration to process |
| `DEPRESSION_THRESHOLD` | `0.5` | Risk classification threshold |

## Testing

```bash
curl -X POST "http://localhost:8001/api/ml/depression" \
  -F "file=@sample_audio.wav"
```

Expected response:
```json
{
  "risk": 1,
  "risk_level": "High",
  "risk_probability": 0.82,
  "risk_confidence": 0.82,
  "segment_count": 3
}
```

## Troubleshooting

**Model not found:**
- Ensure `random_forest_model.pkl` exists in `model_store/`
- Check `DEPRESSION_MODEL_PATH` environment variable

**Audio processing errors:**
- Verify ffmpeg is installed
- Supported formats: wav, mp3
- Recording must be at least `MIN_RECORDING_DURATION_SECONDS` long

## License

Part of the Mental Health Monitoring System (mHealth) thesis project.
