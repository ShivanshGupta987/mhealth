from fastapi import APIRouter, File, UploadFile, HTTPException
from app.ml_client import get_ml_client

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.post("/depression")
async def predict_depression(file: UploadFile = File(...), threshold: float = 0.5):
    """Proxy: predict depression risk from an audio file via the ML microservice."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    try:
        audio_bytes = await file.read()
        ml_client = get_ml_client()
        result = ml_client.predict_depression_from_bytes(audio_bytes, threshold=threshold)
        if result is None:
            raise HTTPException(status_code=503, detail="ML service unavailable or prediction failed")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML service error: {str(e)}")


@router.get("/health")
async def ml_service_health():
    """Check ML service health status."""
    try:
        ml_client = get_ml_client()
        is_healthy = ml_client.health_check()
        if is_healthy:
            return {"status": "healthy", "service": "ml-service"}
        return {"status": "unhealthy", "service": "ml-service"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ML service unavailable: {str(e)}")

