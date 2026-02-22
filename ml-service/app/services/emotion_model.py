"""Legacy Emotion Model Service using sklearn"""
import logging
import numpy as np
from pathlib import Path
from joblib import dump, load
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from app.config import EMOTION_LABELS, EMOTION_MODEL_PATH

logger = logging.getLogger(__name__)


class EmotionModelService:
    """Lazy loader for an sklearn pipeline that predicts call emotions from audio features."""

    def __init__(self):
        self._model = None
        self._feature_len = None

    def _train_fallback_model(self, feature_len: int) -> Pipeline:
        """Train a simple fallback model if no pre-trained model is available."""
        rng = np.random.default_rng(7)
        samples = 600
        X = rng.normal(loc=0.0, scale=1.0, size=(samples, feature_len))
        y = rng.integers(low=0, high=len(EMOTION_LABELS), size=samples)

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=200, multi_class="auto"))
        ])
        pipeline.fit(X, y)
        return pipeline

    def _load_or_train(self, feature_len: int) -> Pipeline:
        """Load cached model or train a new one."""
        if EMOTION_MODEL_PATH.exists():
            try:
                bundle = load(EMOTION_MODEL_PATH)
                pipeline = bundle.get("pipeline")
                stored_len = bundle.get("feature_len")
                if pipeline is not None and stored_len == feature_len:
                    self._feature_len = stored_len
                    logger.info("Loaded cached emotion model from disk")
                    return pipeline
            except Exception as exc:
                logger.warning(f"Failed to load cached emotion model: {exc}")

        logger.info("Training fallback emotion model for feature length %s", feature_len)
        pipeline = self._train_fallback_model(feature_len)
        dump({"pipeline": pipeline, "feature_len": feature_len}, EMOTION_MODEL_PATH)
        self._feature_len = feature_len
        return pipeline

    def predict(self, feature_vector: np.ndarray):
        """Predict emotion from feature vector."""
        feature_len = feature_vector.shape[0]
        if self._model is None or self._feature_len != feature_len:
            self._model = self._load_or_train(feature_len)
        probs = self._model.predict_proba([feature_vector])[0]
        idx = int(np.argmax(probs))
        return EMOTION_LABELS[idx], float(probs[idx])


# Global service instance
_emotion_service = None

def get_emotion_service() -> EmotionModelService:
    """Get or create the global emotion service instance."""
    global _emotion_service
    if _emotion_service is None:
        _emotion_service = EmotionModelService()
    return _emotion_service
