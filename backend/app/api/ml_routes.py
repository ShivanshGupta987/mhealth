from fastapi import APIRouter, File, UploadFile, HTTPException
from app.ml_client import get_ml_client

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.post("/sentiment")
async def predict_sentiment(file: UploadFile = File(...)):
    """
    Analyze audio sentiment by forwarding to ML microservice.
    
    This endpoint acts as a proxy to the separate ML service.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    try:
        audio_bytes = await file.read()
        ml_client = get_ml_client()
        result = await ml_client.predict_sentiment(audio_bytes, file.filename or "audio.mp3")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML service error: {str(e)}")


@router.post("/emotion")
async def predict_emotion(file: UploadFile = File(...)):
    """
    Classify emotion by forwarding to ML microservice.
    
    Uses the legacy sklearn-based model.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    try:
        audio_bytes = await file.read()
        ml_client = get_ml_client()
        result = await ml_client.predict_emotion(audio_bytes, file.filename or "audio.mp3")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML service error: {str(e)}")


@router.get("/health")
async def ml_service_health():
    """
    Check ML service health status.
    """
    try:
        ml_client = get_ml_client()
        health_status = await ml_client.health_check()
        return health_status
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ML service unavailable: {str(e)}")

