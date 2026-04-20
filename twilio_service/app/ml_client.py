"""ML Service Client - Depression Risk Prediction

This module interfaces with the ML Service to get depression risk predictions
from call audio recordings.
"""

import logging
import httpx
from typing import Optional, Dict, Any
from app.config import ML_SERVICE_URL

logger = logging.getLogger(__name__)


class MLServiceClient:
    """Client for ML Service API endpoints."""
    
    def __init__(self, base_url: str = ML_SERVICE_URL, timeout: float = 60.0):
        """
        Initialize ML Service client.
        
        Args:
            base_url: Base URL of ML Service (e.g., http://localhost:8001)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def predict_depression_from_url(
        self,
        audio_url: str,
        threshold: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Get depression risk prediction by downloading audio from URL.
        
        Args:
            audio_url: URL to audio file
            threshold: Probability threshold for depression classification
        
        Returns:
            Dictionary with depression prediction results or None on error
        """
        try:
            # Download audio from URL
            logger.info(f"Downloading audio from: {audio_url}")
            audio_response = httpx.get(audio_url, timeout=self.timeout)
            audio_response.raise_for_status()
            audio_bytes = audio_response.content
            
            # Send to ML Service
            return self.predict_depression_from_bytes(audio_bytes, threshold)
        
        except Exception as e:
            logger.error(f"Error predicting depression from URL: {e}", exc_info=True)
            return None
    
    def predict_depression_from_bytes(
        self,
        audio_bytes: bytes,
        threshold: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Get depression risk prediction from audio bytes.
        
        Args:
            audio_bytes: Audio file content (wav, mp3, etc.)
            threshold: Probability threshold for depression classification
        
        Returns:
            Dictionary with depression prediction results or None on error
        """
        try:
            endpoint = f"{self.base_url}/api/ml/depression"
            
            files = {
                'file': ('audio.wav', audio_bytes, 'audio/wav')
            }
            params = {
                'threshold': threshold
            }
            
            logger.info(f"Sending audio to ML Service for depression prediction")
            response = httpx.post(
                endpoint,
                files=files,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Depression prediction successful: {result['risk_level']}")
            return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"ML Service returned error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling depression prediction endpoint: {e}", exc_info=True)
            return None
    
    def health_check(self) -> bool:
        """
        Check if ML Service is running.
        
        Returns:
            True if ML Service is healthy, False otherwise
        """
        try:
            endpoint = f"{self.base_url}/health"
            response = httpx.get(endpoint, timeout=5.0)
            response.raise_for_status()
            health_data = response.json()
            is_healthy = health_data.get('status') == 'healthy'
            logger.info(f"ML Service health check: {'OK' if is_healthy else 'FAILED'}")
            return is_healthy
        except Exception as e:
            logger.warning(f"ML Service health check failed: {e}")
            return False


# Global client instance
_client: Optional[MLServiceClient] = None


def get_client(base_url: str = ML_SERVICE_URL) -> MLServiceClient:
    """
    Get or create ML Service client instance.
    
    Args:
        base_url: Base URL of ML Service
    
    Returns:
        MLServiceClient instance
    """
    global _client
    if _client is None:
        _client = MLServiceClient(base_url)
    return _client
