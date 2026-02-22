"""
ML Service Client - HTTP client for communicating with the separate ML microservice.
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from app.config import ML_SERVICE_URL, ML_SERVICE_TIMEOUT

logger = logging.getLogger(__name__)


class MLServiceClient:
    """Client for calling the ML microservice API."""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or ML_SERVICE_URL
        self.timeout = timeout or ML_SERVICE_TIMEOUT
        logger.info(f"ML Service Client initialized with base URL: {self.base_url}")
    
    async def predict_sentiment(self, audio_bytes: bytes, filename: str = "audio.mp3") -> Dict[str, Any]:
        """
        Analyze audio sentiment using the ML service.
        
        Args:
            audio_bytes: Audio file content as bytes
            filename: Original filename (for content type detection)
            
        Returns:
            Dictionary with vad, emotion, sentiment, and timing information
            
        Raises:
            httpx.HTTPError: If the ML service request fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, audio_bytes, self._get_content_type(filename))}
                response = await client.post(
                    f"{self.base_url}/api/ml/sentiment",
                    files=files
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Sentiment analysis completed: {result['emotion']} ({result['sentiment']})")
                return result
                
        except httpx.TimeoutException:
            logger.error(f"ML service timeout after {self.timeout}s")
            raise Exception(f"ML service request timed out after {self.timeout} seconds")
        except httpx.HTTPError as e:
            logger.error(f"ML service HTTP error: {e}")
            raise Exception(f"ML service request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling ML service: {e}", exc_info=True)
            raise
    
    async def predict_emotion(self, audio_bytes: bytes, filename: str = "audio.mp3") -> Dict[str, Any]:
        """
        Classify emotion using the ML service (legacy sklearn model).
        
        Args:
            audio_bytes: Audio file content as bytes
            filename: Original filename
            
        Returns:
            Dictionary with emotion label and confidence score
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, audio_bytes, self._get_content_type(filename))}
                response = await client.post(
                    f"{self.base_url}/api/ml/emotion",
                    files=files
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Emotion classification: {result['emotion']} (confidence: {result['confidence']})")
                return result
                
        except httpx.TimeoutException:
            logger.error(f"ML service timeout after {self.timeout}s")
            raise Exception(f"ML service request timed out after {self.timeout} seconds")
        except httpx.HTTPError as e:
            logger.error(f"ML service HTTP error: {e}")
            raise Exception(f"ML service request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling ML service: {e}", exc_info=True)
            raise
    
    async def predict_emotion_from_features(self, features: List[float]) -> Dict[str, Any]:
        """
        Classify emotion from pre-extracted feature vector.
        
        Args:
            features: Audio feature vector as list of floats
            
        Returns:
            Dictionary with emotion label and confidence score
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/ml/emotion-from-features",
                    json=features
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Emotion from features: {result['emotion']} (confidence: {result['confidence']})")
                return result
                
        except httpx.TimeoutException:
            logger.error(f"ML service timeout after {self.timeout}s")
            raise Exception(f"ML service request timed out after {self.timeout} seconds")
        except httpx.HTTPError as e:
            logger.error(f"ML service HTTP error: {e}")
            raise Exception(f"ML service request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling ML service: {e}", exc_info=True)
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check ML service health status.
        
        Returns:
            Health status dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"ML service health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def warmup(self) -> Dict[str, Any]:
        """
        Warmup ML service models (pre-load before handling traffic).
        
        Returns:
            Warmup status dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self.base_url}/warmup")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"ML service warmup failed: {e}")
            raise
    
    def _get_content_type(self, filename: str) -> str:
        """Get MIME type from filename extension."""
        suffix = Path(filename).suffix.lower()
        content_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
        }
        return content_types.get(suffix, 'application/octet-stream')


# Global client instance
_ml_client = None

def get_ml_client() -> MLServiceClient:
    """Get or create the global ML service client instance."""
    global _ml_client
    if _ml_client is None:
        _ml_client = MLServiceClient()
    return _ml_client


# Synchronous wrapper for non-async contexts (Celery tasks)
def predict_sentiment_sync(audio_bytes: bytes, filename: str = "audio.mp3") -> Dict[str, Any]:
    """
    Synchronous wrapper for sentiment prediction (for use in Celery tasks).
    
    Args:
        audio_bytes: Audio file content as bytes
        filename: Original filename
        
    Returns:
        Dictionary with vad, emotion, sentiment, and timing information
    """
    import asyncio
    
    try:
        client = get_ml_client()
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(client.predict_sentiment(audio_bytes, filename))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Synchronous sentiment prediction failed: {e}")
        raise


def predict_emotion_sync(audio_bytes: bytes, filename: str = "audio.mp3") -> Dict[str, Any]:
    """
    Synchronous wrapper for emotion prediction (for use in Celery tasks).
    
    Args:
        audio_bytes: Audio file content as bytes
        filename: Original filename
        
    Returns:
        Dictionary with emotion label and confidence score
    """
    import asyncio
    
    try:
        client = get_ml_client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(client.predict_emotion(audio_bytes, filename))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Synchronous emotion prediction failed: {e}")
        raise
