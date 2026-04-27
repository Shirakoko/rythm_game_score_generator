import librosa
import numpy as np


class BeatAnalyzer:
    def analyze(self, y: np.ndarray, sr: int) -> dict:
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        # librosa >= 0.10 may return array
        tempo = float(np.atleast_1d(tempo)[0])
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units="frames")
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        return {
            "tempo": tempo,
            "beat_times": beat_times,
            "onset_times": onset_times,
        }
