"""Run depression prediction on questionnaire_audio_data.zip using the ML service."""
import io
import os
import zipfile
import requests
import numpy as np
import soundfile as sf
import librosa

ML_SERVICE_URL = "http://localhost:8001/api/ml/depression"
ZIP_PATH = "questionnaire_audio_data.zip"


def load_opus_bytes(audio_bytes: bytes) -> tuple:
    """Load opus audio bytes using librosa, return (array, sample_rate)."""
    buf = io.BytesIO(audio_bytes)
    y, sr = librosa.load(buf, sr=16000, mono=True)
    return y, sr


def combine_user_audio(file_map: dict) -> bytes:
    """Concatenate all audio arrays for a user and return as WAV bytes."""
    arrays = []
    sr = 16000
    for filename in sorted(file_map.keys()):
        y, _ = load_opus_bytes(file_map[filename])
        arrays.append(y)
    combined = np.concatenate(arrays)
    buf = io.BytesIO()
    sf.write(buf, combined, sr, format="WAV")
    return buf.getvalue()


def predict(wav_bytes: bytes) -> dict:
    """Send WAV bytes to ML service and return prediction result."""
    response = requests.post(
        ML_SERVICE_URL,
        files={"file": ("audio.wav", wav_bytes, "audio/wav")},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def main():
    print(f"{'User':<10} {'Risk':<6} {'Probability':<14} {'Level':<8} {'Confidence':<12} {'Segments'}")
    print("-" * 65)

    results = []

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        # Group files by user folder
        user_files: dict[str, dict] = {}
        for name in zf.namelist():
            if name.endswith(".opus"):
                parts = name.split("/")
                user = parts[1]   # e.g. User1
                filename = parts[2]
                if user not in user_files:
                    user_files[user] = {}
                user_files[user][filename] = zf.read(name)

        for user in sorted(user_files.keys(), key=lambda u: int(u.replace("User", ""))):
            try:
                wav_bytes = combine_user_audio(user_files[user])
                result = predict(wav_bytes)
                results.append({"user": user, **result})
                print(
                    f"{user:<10} {result['depression_risk']:<6} "
                    f"{result['risk_probability']:<14.4f} "
                    f"{result['risk_level']:<8} "
                    f"{result['confidence']:<12.4f} "
                    f"{result['num_segments']}"
                )
            except Exception as e:
                print(f"{user:<10} ERROR: {e}")

    # Summary
    depressed = [r for r in results if r["depression_risk"] == 1]
    print("-" * 65)
    print(f"\nSummary: {len(depressed)}/{len(results)} users predicted as depressed (risk=1)")
    print(f"Average probability: {np.mean([r['risk_probability'] for r in results]):.4f}")


if __name__ == "__main__":
    main()
