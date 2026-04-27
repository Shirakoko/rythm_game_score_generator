import numpy as np


class StructureAnalyzer:
    """Energy-based segment classification (silence / verse / chorus)."""

    HIGH_THRESHOLD = 0.6
    LOW_THRESHOLD = 0.3

    def analyze(self, energy_data: dict, segment_duration: float = 5.0) -> list[dict]:
        times = energy_data["times"]
        energy = energy_data["energy"]
        total = float(times[-1]) if len(times) > 0 else 0.0

        segments = []
        t = 0.0
        while t < total:
            end_t = min(t + segment_duration, total)
            mask = (times >= t) & (times < end_t)
            mean_e = float(np.mean(energy[mask])) if np.any(mask) else 0.0

            if mean_e >= self.HIGH_THRESHOLD:
                seg_type = "chorus"
            elif mean_e <= self.LOW_THRESHOLD:
                seg_type = "silence"
            else:
                seg_type = "verse"

            segments.append({"start": t, "end": end_t, "type": seg_type, "energy": mean_e})
            t = end_t

        return segments
