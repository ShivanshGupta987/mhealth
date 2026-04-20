# ML Service

A standalone microservice for machine learning inference, providing emotion and sentiment analysis from audio recordings.

## Features

- **VAD-based Sentiment Analysis**: Deep learning model using Wav2Vec2 LSTM for emotion detection
- **Legacy Emotion Classification**: sklearn-based model with librosa feature extraction
- **RESTful API**: FastAPI-based endpoints for easy integration
- **Docker Support**: Containerized deployment for scalability
- **Health Monitoring**: Built-in health check endpoints

## API Endpoints

### Sentiment Analysis
```
POST /api/ml/sentiment
- Upload audio file
- Returns: VAD coordinates, emotion, sentiment, timing
```

### Emotion Classification
```
POST /api/ml/emotion
- Upload audio file  
- Returns: emotion label, confidence score
```

### Emotion from Features
```
POST /api/ml/emotion-from-features
- Send pre-extracted feature vector
- Returns: emotion label, confidence score
```

### Health Check
```
GET /health
- Returns service status and model loading state
```

## Quick Start

### Local Development

1. **Install dependencies:**
```bash
cd ml-service
pip install -r requirements.txt
```

2. **Copy model files:**
Ensure `best_model.pt` is in `model_store/` directory

3. **Run the service:**
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### Docker Deployment

1. **Build the image:**
```bash
docker build -t mhealth-ml-service .
```

2. **Run the container:**
```bash
docker run -p 8001:8001 \
  -v $(pwd)/model_store:/app/model_store \
  mhealth-ml-service
```

### Using Docker Compose

From the project root directory:
```bash
docker compose up ml-service
```

## Configuration

Environment variables (see `.env.example`):

- `ML_SERVICE_HOST`: Host to bind to (default: 0.0.0.0)
- `ML_SERVICE_PORT`: Port to listen on (default: 8001)
- `SENTIMENT_MODEL_PATH`: Path to PyTorch model file
- `TARGET_SAMPLE_RATE`: Audio sample rate (default: 16000 Hz)
- `MAX_AUDIO_DURATION`: Maximum audio duration (default: 5.27s)

## Model Requirements

### VAD Sentiment Model
- **File**: `best_model.pt` in `model_store/`
- **Architecture**: Wav2Vec2 + LSTM
- **Input**: Raw audio (automatically resampled to 16kHz)
- **Output**: VAD coordinates, emotion label, sentiment

### Emotion Classification Model
- **File**: `emotion_model.joblib` (auto-generated if missing)
- **Architecture**: sklearn Logistic Regression pipeline
- **Input**: Librosa-extracted audio features
- **Output**: POSITIVE/NEGATIVE/NEUTRAL with confidence

## Testing

Test the sentiment endpoint:
```bash
curl -X POST "http://localhost:8001/api/ml/sentiment" \
  -F "file=@sample_audio.mp3"
```

Expected response:
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

## Integration with Main Backend

The main backend should call this service via HTTP:

```python
import httpx

async def analyze_sentiment(audio_bytes: bytes):
    async with httpx.AsyncClient() as client:
        files = {"file": ("audio.mp3", audio_bytes, "audio/mpeg")}
        response = await client.post(
            "http://ml-service:8001/api/ml/sentiment",
            files=files,
            timeout=30.0
        )
        return response.json()
```

## Performance Considerations

- **Model Loading**: Models are lazy-loaded on first request
- **GPU Support**: Automatically uses CUDA if available
- **Concurrent Requests**: Handle multiple requests simultaneously
- **Caching**: Consider adding Redis for repeated predictions

## Monitoring

Access service metrics:
- Health: `GET /health`
- Root: `GET /`
- Warmup: `POST /warmup` (pre-load models)

## Troubleshooting

**Model not found:**
- Ensure `best_model.pt` exists in `model_store/`
- Check `SENTIMENT_MODEL_PATH` environment variable

**Audio processing errors:**
- Verify ffmpeg is installed
- Check audio file format (wav, mp3 supported)
- Ensure valid audio content

**Memory issues:**
- Reduce batch size or max audio duration
- Consider CPU-only deployment if GPU memory limited
- Monitor with `docker stats`

## License

Part of the Mental Health Monitoring System (mHealth) thesis project.
