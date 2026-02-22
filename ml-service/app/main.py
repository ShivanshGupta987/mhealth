"""
ML Service - Standalone FastAPI application for machine learning inference.

This service provides endpoints for:
- VAD-based sentiment analysis from audio
- Legacy emotion classification from audio features
- Health checks and service status
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import Dict, List, Optional
import numpy as np

from app.services.vad_sentiment import get_service as get_vad_service
from app.services.emotion_model import get_emotion_service
from app.services.audio_utils import extract_features_from_bytes
from app.config import ML_SERVICE_HOST, ML_SERVICE_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mental Health ML Service",
    description="Machine learning inference service for emotion and sentiment analysis",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
_vad_service = None
_emotion_service = None


def get_vad_service_instance():
    """Lazy initialization of VAD sentiment service."""
    global _vad_service
    if _vad_service is None:
        logger.info("Initializing VAD Sentiment Service...")
        _vad_service = get_vad_service()
        logger.info("VAD Sentiment Service initialized successfully")
    return _vad_service


def get_emotion_service_instance():
    """Lazy initialization of emotion model service."""
    global _emotion_service
    if _emotion_service is None:
        logger.info("Initializing Emotion Model Service...")
        _emotion_service = get_emotion_service()
        logger.info("Emotion Model Service initialized successfully")
    return _emotion_service


# Response models
class SentimentResponse(BaseModel):
    """Response model for sentiment analysis."""
    vad: List[float]
    emotion: str
    sentiment: str
    timing: Dict[str, float]


class EmotionResponse(BaseModel):
    """Response model for emotion classification."""
    emotion: str
    confidence: float


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service: str
    version: str
    models_loaded: Dict[str, bool]


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "service": "MHealth ML service is successfully up",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="ml-service",
        version="1.0.0",
        models_loaded={
            "vad_sentiment": _vad_service is not None,
            "emotion_model": _emotion_service is not None
        }
    )


@app.post("/api/ml/sentiment", response_model=SentimentResponse)
async def predict_sentiment(file: UploadFile = File(...)):
    """
    Analyze audio sentiment using VAD-based deep learning model.
    
    Args:
        file: Audio file (mp3, wav, etc.)
        
    Returns:
        VAD coordinates, emotion label, and sentiment classification
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        logger.info(f"Processing sentiment analysis for file: {file.filename}")
        audio_bytes = await file.read()
        
        service = get_vad_service_instance()
        result = service.predict(audio_bytes)
        
        logger.info(f"Sentiment analysis completed: {result['emotion']} ({result['sentiment']})")
        return SentimentResponse(**result)
        
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/api/ml/emotion", response_model=EmotionResponse)
async def predict_emotion(file: UploadFile = File(...)):
    """
    Classify emotion using legacy sklearn model with librosa features.
    
    Args:
        file: Audio file (mp3, wav, etc.)
        
    Returns:
        Emotion label and confidence score
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        logger.info(f"Processing emotion classification for file: {file.filename}")
        audio_bytes = await file.read()
        
        # Extract audio features
        feature_vector = extract_features_from_bytes(audio_bytes)
        
        # Get prediction
        service = get_emotion_service_instance()
        emotion_label, confidence = service.predict(feature_vector)
        
        logger.info(f"Emotion classification completed: {emotion_label} (confidence: {confidence:.3f})")
        return EmotionResponse(emotion=emotion_label, confidence=confidence)
        
    except Exception as e:
        logger.error(f"Emotion classification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/api/ml/emotion-from-features", response_model=EmotionResponse)
async def predict_emotion_from_features(features: List[float]):
    """
    Classify emotion from pre-extracted feature vector.
    
    Args:
        features: Audio feature vector as list of floats
        
    Returns:
        Emotion label and confidence score
    """
    try:
        logger.info(f"Processing emotion classification from {len(features)} features")
        
        # Convert to numpy array
        feature_vector = np.array(features)
        
        # Get prediction
        service = get_emotion_service_instance()
        emotion_label, confidence = service.predict(feature_vector)
        
        logger.info(f"Emotion classification completed: {emotion_label} (confidence: {confidence:.3f})")
        return EmotionResponse(emotion=emotion_label, confidence=confidence)
        
    except Exception as e:
        logger.error(f"Emotion classification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/warmup")
async def warmup():
    """
    Warmup endpoint to initialize models before receiving real traffic.
    Useful for container orchestration and health checks.
    """
    try:
        logger.info("Warming up models...")
        get_vad_service_instance()
        get_emotion_service_instance()
        logger.info("Model warmup completed successfully")
        return {"status": "models warmed up", "success": True}
    except Exception as e:
        logger.error(f"Model warmup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Warmup failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=ML_SERVICE_HOST,
        port=ML_SERVICE_PORT,
        log_level="info"
    )
