"""Configuration for ML Service"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model configuration
SENTIMENT_MODEL_PATH = os.getenv("SENTIMENT_MODEL_PATH", "./model_store/best_model_state_legacy.pt")
EMOTION_MODEL_PATH = Path(__file__).resolve().parent / "emotion_model.joblib"

# Audio processing configuration
TARGET_SAMPLE_RATE = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))
MAX_AUDIO_DURATION = float(os.getenv("MAX_AUDIO_DURATION", "5.27"))
MIN_RECORDING_DURATION_SECONDS = int(os.getenv("MIN_RECORDING_DURATION_SECONDS", "3"))

# Service configuration
ML_SERVICE_HOST = os.getenv("ML_SERVICE_HOST", "0.0.0.0")
ML_SERVICE_PORT = int(os.getenv("ML_SERVICE_PORT", "8001"))

# Model labels
EMOTION_LABELS = ["NEGATIVE", "POSITIVE", "NEUTRAL"]
