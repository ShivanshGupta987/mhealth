"""
Depression Risk Prediction Service

Uses Random Forest model on TSFEL-extracted audio features to predict depression risk.
Implements segment-level and subject-level prediction aggregation.
"""

import os
import logging
import numpy as np
import librosa
import tsfel
import joblib
from pathlib import Path
from typing import Optional, Dict, Tuple, List

logger = logging.getLogger(__name__)


class DepressionPredictionService:
    """Service for depression risk prediction from audio."""
    
    def __init__(self, model_path: str, sr: int = 16000, segment_duration: float = 7.0):
        """
        Initialize depression prediction service.
        
        Args:
            model_path: Path to trained Random Forest model (pkl)
            sr: Sample rate for audio processing
            segment_duration: Duration of audio segments in seconds
        """
        self.model_path = model_path
        self.sr = sr
        self.segment_duration = segment_duration
        self.model = None
        self.tsfel_config = None
        self._load_model()
        self._load_tsfel_config()
    
    def _load_model(self):
        """Load Random Forest model from disk."""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info(f"Depression model loaded from {self.model_path}")
            else:
                logger.warning(f"Model path {self.model_path} not found. Model will be None.")
        except Exception as e:
            logger.error(f"Error loading depression model: {e}")
            self.model = None
    
    def _load_tsfel_config(self):
        """Load TSFEL feature extractor configuration."""
        try:
            self.tsfel_config = tsfel.get_features_by_domain()
            logger.info("TSFEL configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading TSFEL config: {e}")
            self.tsfel_config = None
    
    def segment_audio(self, y: np.ndarray) -> List[np.ndarray]:
        """
        Segment audio into fixed-length chunks.
        
        Args:
            y: Audio signal
        
        Returns:
            List of audio segments (padded to same length if needed)
        """
        seg_samples = int(self.segment_duration * self.sr)
        segments = []
        
        for i in range(0, len(y), seg_samples):
            seg = y[i:i + seg_samples]
            # Pad segment if shorter than target length
            if len(seg) < seg_samples:
                seg = np.pad(seg, (0, seg_samples - len(seg)))
            segments.append(seg)
        
        return segments
    
    def extract_tsfel_features(self, y: np.ndarray) -> np.ndarray:
        """
        Extract TSFEL features from audio.
        
        Args:
            y: Audio signal
        
        Returns:
            Array of aggregated features [624 features: 156*4 (mean, std, min, max)]
        """
        if self.tsfel_config is None:
            raise RuntimeError("TSFEL config not loaded")
        
        # Segment the audio
        segments = self.segment_audio(y)
        all_features = []
        
        for seg in segments:
            # TSFEL expects (N, channels) shape
            seg_reshaped = seg.reshape(-1, 1)
            try:
                features = tsfel.time_series_features_extractor(
                    self.tsfel_config, seg_reshaped, fs=self.sr, verbose=0
                )
                all_features.append(features.values.squeeze())
            except Exception as e:
                logger.error(f"Error extracting TSFEL features: {e}")
                continue
        
        if len(all_features) == 0:
            raise RuntimeError("Failed to extract features from any segment")
        
        # Aggregate features across segments (mean, std, min, max)
        features_array = np.vstack(all_features)
        aggregated = np.concatenate([
            np.mean(features_array, axis=0),  # 156 features
            np.std(features_array, axis=0),   # 156 features
            np.min(features_array, axis=0),   # 156 features
            np.max(features_array, axis=0),   # 156 features
        ])
        
        return aggregated
    
    def predict_segment_level(self, y: np.ndarray) -> Dict:
        """
        Make segment-level depression predictions.
        
        Args:
            y: Audio signal
        
        Returns:
            Dictionary with segment-level predictions and probabilities
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Segment audio and extract features
        segments = self.segment_audio(y)
        segment_features = []
        
        for seg in segments:
            seg_reshaped = seg.reshape(-1, 1)
            try:
                features = tsfel.time_series_features_extractor(
                    self.tsfel_config, seg_reshaped, fs=self.sr, verbose=0
                )
                segment_features.append(features.values.squeeze())
            except Exception as e:
                logger.error(f"Error extracting features: {e}")
                continue
        
        if len(segment_features) == 0:
            raise RuntimeError("Failed to extract features from any segment")
        
        X = np.array(segment_features)
        
        # Get predictions
        y_pred = self.model.predict(X)
        y_probs = self.model.predict_proba(X)[:, 1]  # Probability of depression (class 1)
        
        return {
            "num_segments": len(X),
            "predictions": y_pred.tolist(),
            "probabilities": y_probs.tolist(),
            "mean_probability": float(np.mean(y_probs)),
            "std_probability": float(np.std(y_probs)),
            "risk_level": "High" if np.mean(y_probs) >= 0.5 else "Low"
        }
    
    def predict_subject_level(self, y: np.ndarray, threshold: float = 0.5) -> Dict:
        """
        Make subject-level depression prediction by aggregating segment predictions.
        
        Args:
            y: Audio signal
            threshold: Probability threshold for classification (default 0.5)
        
        Returns:
            Dictionary with subject-level aggregated prediction
        """
        # Get segment-level results
        segment_results = self.predict_segment_level(y)
        
        # Aggregate to subject level
        mean_prob = segment_results["mean_probability"]
        prediction = 1 if mean_prob >= threshold else 0
        
        return {
            "depression_risk": prediction,
            "risk_probability": mean_prob,
            "risk_level": "High" if prediction == 1 else "Low",
            "confidence": max(mean_prob, 1 - mean_prob),
            "num_segments": segment_results["num_segments"],
            "segment_details": segment_results
        }
    
    def predict_from_audio_bytes(
        self, audio_bytes: bytes, threshold: float = 0.5
    ) -> Dict:
        """
        Make depression prediction from audio bytes.
        
        Args:
            audio_bytes: Audio file content
            threshold: Probability threshold for classification
        
        Returns:
            Dictionary with depression prediction results
        """
        try:
            # Load audio from bytes
            import io
            audio_file = io.BytesIO(audio_bytes)
            y, sr = librosa.load(audio_file, sr=self.sr)
            
            # Resample if necessary
            if sr != self.sr:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.sr)
            
            # Normalize
            y = librosa.util.normalize(y)
            
            # Make prediction
            result = self.predict_subject_level(y, threshold)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def predict_from_file(
        self, file_path: str, threshold: float = 0.5
    ) -> Dict:
        """
        Make depression prediction from audio file.
        
        Args:
            file_path: Path to audio file
            threshold: Probability threshold for classification
        
        Returns:
            Dictionary with depression prediction results
        """
        try:
            # Load audio
            y, sr = librosa.load(file_path, sr=self.sr)
            
            # Normalize
            y = librosa.util.normalize(y)
            
            # Make prediction
            result = self.predict_subject_level(y, threshold)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global service instance
_service: Optional[DepressionPredictionService] = None


def get_service(
    model_path: str = None,
    sr: int = 16000,
    segment_duration: float = 8.0
) -> DepressionPredictionService:
    """
    Get or create depression prediction service instance.
    
    Args:
        model_path: Path to trained model
        sr: Sample rate
        segment_duration: Segment duration in seconds
    
    Returns:
        DepressionPredictionService instance
    """
    global _service
    
    if _service is None:
        from app.config import DEPRESSION_MODEL_PATH, TARGET_SAMPLE_RATE, SEGMENT_DURATION
        _service = DepressionPredictionService(
            model_path=model_path or DEPRESSION_MODEL_PATH,
            sr=sr or TARGET_SAMPLE_RATE,
            segment_duration=segment_duration or SEGMENT_DURATION
        )
    
    return _service
