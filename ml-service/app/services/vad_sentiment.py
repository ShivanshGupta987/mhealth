import io
import time
import numpy as np
import torch
import torch.nn as nn
import torchaudio
import soundfile as sf
from pathlib import Path
from transformers import Wav2Vec2Model, Wav2Vec2FeatureExtractor
from app.config import SENTIMENT_MODEL_PATH


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

torch.set_num_threads(max(1, torch.get_num_threads()))


emotion_to_vad_map = {
    'Neutral':  [0.883, 0.170, 0.304],
    'Calm':     [0.744, 0.085, 0.191],
    'Happy':    [0.987, 0.529, 0.596],
    'Sad':      [0.736, 0.305, 0.401],
    'Angry':    [0.235, 0.863, 0.918],
    'Anxious':  [0.431, 0.607, 0.415],
    'Disgust':  [0.397, 0.386, 0.493],
    'Surprised':[0.709, 0.623, 0.683],
}

sentiment_map = {
    'Happy': 'Positive',
    'Neutral': 'Neutral',
    'Calm': 'Neutral',
    'Surprised': 'Neutral',
    'Sad': 'Negative',
    'Angry': 'Negative',
    'Anxious': 'Negative',
    'Disgust': 'Negative',
}


class Wav2Vec2_LSTM_VAD(nn.Module):
    def __init__(self, pretrained_model_name='ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition'):
        super().__init__()
        self.wav2vec = Wav2Vec2Model.from_pretrained(pretrained_model_name)
        self.wav2vec.eval()
        self.lstm = nn.LSTM(input_size=1024, hidden_size=256, batch_first=True)
        self.fc1 = nn.Linear(256, 256)
        self.fc2 = nn.Linear(256, 256)
        self.out = nn.Linear(256, 3)

    def forward(self, input_values, attention_mask=None):
        with torch.no_grad():
            wav2vec_out = self.wav2vec(input_values, attention_mask=attention_mask).last_hidden_state
        lstm_out, _ = self.lstm(wav2vec_out)
        last_hidden = lstm_out[:, -1, :]
        x = self.fc1(last_hidden)
        x = self.fc2(x)
        vad_out = self.out(x)
        return vad_out


class VADSentimentService:
    def __init__(self, model_path: str | None = None, target_sr: int = 16000, max_duration: float = 5.27):
        self.device = device
        self.target_sr = target_sr
        self.max_duration = max_duration
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
            "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
        )
        resolved_path = self._resolve_model_path(model_path)
        self.model = Wav2Vec2_LSTM_VAD().to(self.device)
        print(f"Loading model from: {resolved_path}", flush=True)
        state = self._load_state(resolved_path)
        self.model.load_state_dict(state)
        self.model.eval()
 
    def _resolve_model_path(self, model_path: str | None) -> Path:
        if model_path:
            p = Path(model_path)
        else:
            base = Path(__file__).resolve().parents[2]  # ml-service/
            p = base / "model_store" / "best_model.pt"
        if not p.exists():
            raise FileNotFoundError(f"Model file not found at {p}")
        return p

    def _load_state(self, resolved_path: str):
        # Prefer weights_only to avoid torchcodec dependency from torch.package archives.
        try:
            return torch.load(
                resolved_path,
                map_location=self.device,
                weights_only=True,
            )
        except TypeError:
            # Older torch without weights_only flag.
            return torch.load(resolved_path, map_location=self.device)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load checkpoint at {resolved_path}. "
                "If this was saved with torch.package, re-save using torch.save(..., _use_new_zipfile_serialization=False)."
            ) from exc

    def _closest_emotion(self, vad_vec):
        vad = np.array(vad_vec)
        best_label, best_dist = None, 1e9
        for label, ref in emotion_to_vad_map.items():
            dist = np.linalg.norm(vad - np.array(ref))
            if dist < best_dist:
                best_dist = dist
                best_label = label
        return best_label

    def predict(self, audio_bytes: bytes):
        start_time = time.time()
        
        # Use soundfile to avoid torchcodec dependency
        load_start = time.time()
        wav, sr = sf.read(io.BytesIO(audio_bytes))
        load_time = time.time() - load_start
        
        # Convert to mono if stereo
        preprocess_start = time.time()
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        # Resample if needed
        if sr != self.target_sr:
            waveform = torch.from_numpy(wav).unsqueeze(0).float()
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=self.target_sr)
            waveform = resampler(waveform)
            wav = waveform.squeeze(0).numpy()
            sr = self.target_sr
        # Normalize
        wav_tensor = torch.from_numpy(wav).unsqueeze(0)
        wav_tensor = torch.nn.functional.layer_norm(wav_tensor, wav_tensor.shape)
        wav = wav_tensor.squeeze(0).numpy()
        preprocess_time = time.time() - preprocess_start

        feature_start = time.time()
        inputs = self.feature_extractor(
            wav,
            sampling_rate=sr,
            return_tensors="pt",
            padding="max_length",
            max_length=int(self.max_duration * sr),
            truncation=True,
        )
        input_values = inputs.input_values.to(self.device)
        attention_mask = inputs.attention_mask.to(self.device)
        feature_time = time.time() - feature_start

        inference_start = time.time()
        with torch.no_grad():
            vad_out = self.model(input_values, attention_mask=attention_mask)
        vad_vec = vad_out.cpu().numpy()[0].tolist()
        inference_time = time.time() - inference_start

        postprocess_start = time.time()
        emotion = self._closest_emotion(vad_vec)
        sentiment = sentiment_map.get(emotion, "Neutral")
        postprocess_time = time.time() - postprocess_start
        
        total_time = time.time() - start_time
        
        print(f"Timing breakdown - Load: {load_time:.3f}s, Preprocess: {preprocess_time:.3f}s, "
              f"Features: {feature_time:.3f}s, Inference: {inference_time:.3f}s, "
              f"Postprocess: {postprocess_time:.3f}s, Total: {total_time:.3f}s", flush=True)
        
        return {
            "vad": vad_vec,
            "emotion": emotion,
            "sentiment": sentiment,
            "timing": {
                "load_time": round(load_time, 3),
                "preprocess_time": round(preprocess_time, 3),
                "feature_extraction_time": round(feature_time, 3),
                "inference_time": round(inference_time, 3),
                "postprocess_time": round(postprocess_time, 3),
                "total_time": round(total_time, 3)
            }
        }


def get_service() -> VADSentimentService:
    return VADSentimentService(model_path=SENTIMENT_MODEL_PATH)
