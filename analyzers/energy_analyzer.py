import librosa
import numpy as np


class EnergyAnalyzer:
    def analyze(self, y: np.ndarray, sr: int) -> dict:
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)

        rms_max = float(np.max(rms)) if np.max(rms) > 0 else 1.0
        rms_norm = rms / rms_max

        # Smooth with a sliding window (~0.5 s)
        frames_per_second = sr / 512  # default hop_length
        window = max(1, int(frames_per_second * 0.5))
        kernel = np.ones(window) / window
        rms_smooth = np.convolve(rms_norm, kernel, mode="same")

        return {"times": times, "energy": rms_smooth}

    def get_energy_at(self, energy_data: dict, t: float) -> float:
        times = energy_data["times"]
        energy = energy_data["energy"]
        idx = int(np.searchsorted(times, t))
        idx = min(idx, len(energy) - 1)
        return float(energy[idx])
