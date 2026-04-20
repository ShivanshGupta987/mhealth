"""Configuration for ML Service"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model configuration
DEPRESSION_MODEL_PATH = os.getenv("DEPRESSION_MODEL_PATH", "./model_store/random_forest_model.pkl")

# Audio processing configuration
TARGET_SAMPLE_RATE = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))
MAX_AUDIO_DURATION = float(os.getenv("MAX_AUDIO_DURATION", "5.27"))
MIN_RECORDING_DURATION_SECONDS = int(os.getenv("MIN_RECORDING_DURATION_SECONDS", "3"))
SEGMENT_DURATION = float(os.getenv("SEGMENT_DURATION", "7.0"))  # 7-second segments for depression model

# Service configuration
ML_SERVICE_HOST = os.getenv("ML_SERVICE_HOST", "0.0.0.0")
ML_SERVICE_PORT = int(os.getenv("ML_SERVICE_PORT", "8001"))

# Model threshold
DEPRESSION_THRESHOLD = float(os.getenv("DEPRESSION_THRESHOLD", "0.5"))  # Default threshold for depression risk
