"""ML Service - FastAPI application for depression risk inference."""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import Dict, List, Optional

from app.services.depression_prediction import get_service as get_depression_service
from app.config import ML_SERVICE_HOST, ML_SERVICE_PORT, DEPRESSION_THRESHOLD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mental Health ML Service",
    description="Machine learning inference service for depression risk prediction",
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
_depression_service = None


def get_depression_service_instance():
    """Lazy initialization of depression prediction service."""
    global _depression_service
    if _depression_service is None:
        logger.info("Initializing Depression Prediction Service...")
        _depression_service = get_depression_service()
        logger.info("Depression Prediction Service initialized successfully")
    return _depression_service


class DepressionSegmentDetails(BaseModel):
    """Segment-level depression prediction details."""
    num_segments: int
    predictions: List[int]
    probabilities: List[float]
    mean_probability: float
    std_probability: float
    risk_level: str


class DepressionPredictionResponse(BaseModel):
    """Response model for depression risk prediction."""
    depression_risk: int  # 0 or 1
    risk_probability: float  # 0.0-1.0
    risk_level: str  # "High" or "Low"
    confidence: float
    num_segments: int
    segment_details: Optional[DepressionSegmentDetails] = None


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
            "depression_prediction": _depression_service is not None
        }
    )


@app.post("/api/ml/depression", response_model=DepressionPredictionResponse)
async def predict_depression(
    file: UploadFile = File(...),
    threshold: float = DEPRESSION_THRESHOLD
):
    """
    Predict depression risk from audio using Random Forest model on TSFEL features.
    
    Args:
        file: Audio file (mp3, wav, etc.)
        threshold: Probability threshold for depression classification (default 0.5)
        
    Returns:
        Depression risk prediction with probability score and confidence
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        logger.info(f"Processing depression prediction for file: {file.filename}")
        audio_bytes = await file.read()
        
        service = get_depression_service_instance()
        result = service.predict_from_audio_bytes(audio_bytes, threshold=threshold)
        
        if result["status"] != "success":
            raise Exception(result.get("error", "Unknown error"))
        
        data = result["data"]
        logger.info(
            f"Depression prediction completed: Risk={data['risk_level']} "
            f"(Probability: {data['risk_probability']:.3f})"
        )
        
        return DepressionPredictionResponse(**data)
        
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        raise HTTPException(status_code=500, detail=f"Model not found: {str(e)}")
    except Exception as e:
        logger.error(f"Depression prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/api/ml/depression-batch")
async def predict_depression_batch(files: List[UploadFile] = File(...)):
    """
    Predict depression risk for multiple audio files.
    
    Args:
        files: Multiple audio files
        
    Returns:
        List of depression predictions
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    results = []
    
    try:
        service = get_depression_service_instance()
        
        for file in files:
            logger.info(f"Processing batch depression prediction for file: {file.filename}")
            audio_bytes = await file.read()
            
            result = service.predict_from_audio_bytes(audio_bytes, threshold=DEPRESSION_THRESHOLD)
            
            if result["status"] == "success":
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "prediction": result["data"]
                })
            else:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": result.get("error", "Unknown error")
                })
        
        logger.info(f"Batch depression prediction completed for {len(files)} files")
        return {"results": results, "total": len(files), "successful": sum(1 for r in results if r["status"] == "success")}
        
    except Exception as e:
        logger.error(f"Batch depression prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@app.post("/warmup")
async def warmup():
    """
    Warmup endpoint to initialize models before receiving real traffic.
    Useful for container orchestration and health checks.
    """
    try:
        logger.info("Warming up models...")
        get_depression_service_instance()
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
