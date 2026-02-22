"""Audio feature extraction utilities"""
import librosa
import numpy as np
import tempfile
from pathlib import Path


def extract_audio_features(audio_path: str | Path) -> np.ndarray:
    """
    Extract audio features from a file using librosa.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Feature vector as numpy array
    """
    y, sr = librosa.load(audio_path, sr=None)
    
    # Extract various audio features
    features = []
    
    # MFCCs (Mel-frequency cepstral coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features.append(mfccs.mean(axis=1))
    features.append(mfccs.std(axis=1))
    
    # Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)
    features.append([zcr.mean(), zcr.std()])
    
    # Spectral centroid
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    features.append([spectral_centroid.mean(), spectral_centroid.std()])
    
    # Spectral rolloff
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    features.append([spectral_rolloff.mean(), spectral_rolloff.std()])
    
    # Chroma features
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    features.append(chroma.mean(axis=1))
    
    # Flatten all features into a single vector
    feature_vector = np.concatenate([np.array(f).flatten() for f in features])
    
    return feature_vector


def extract_features_from_bytes(audio_bytes: bytes) -> np.ndarray:
    """
    Extract audio features from audio bytes.
    
    Args:
        audio_bytes: Audio data as bytes
        
    Returns:
        Feature vector as numpy array
    """
    # Write bytes to temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name
    
    try:
        return extract_audio_features(tmp_path)
    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)
