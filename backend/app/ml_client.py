"""ML Service Client - HTTP client for the ML microservice (depression prediction)."""
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import ML_SERVICE_TIMEOUT, ML_SERVICE_URL

logger = logging.getLogger(__name__)


class MLServiceClient:
    """Synchronous HTTP client for the ML microservice."""

    def __init__(self, base_url: str = ML_SERVICE_URL, timeout: float = ML_SERVICE_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)

    def predict_depression_from_bytes(
        self, audio_bytes: bytes, threshold: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """Predict depression risk from raw audio bytes.

        Returns the prediction dict on success, None on any error.
        """
        try:
            response = httpx.post(
                f"{self.base_url}/api/ml/depression",
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                params={"threshold": threshold},
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            logger.info("Depression prediction: %s (p=%.3f)", result["risk_level"], result["risk_probability"])
            return result
        except httpx.HTTPStatusError as e:
            logger.error("ML service HTTP %s: %s", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            logger.error("ML service call failed: %s", e, exc_info=True)
            return None

    def health_check(self) -> bool:
        """Return True if the ML service is healthy."""
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=5.0)
            response.raise_for_status()
            return response.json().get("status") == "healthy"
        except Exception as e:
            logger.warning("ML service health check failed: %s", e)
            return False


_ml_client: Optional[MLServiceClient] = None


def get_ml_client() -> MLServiceClient:
    """Return the shared MLServiceClient singleton."""
    global _ml_client
    if _ml_client is None:
        _ml_client = MLServiceClient()
    return _ml_client
