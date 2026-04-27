import random
import numpy as np


class NoteMapper:
    # Minimum onset gap to trigger a hold note
    HOLD_GAP_THRESHOLD = 0.35  # seconds

    def generate(
        self,
        beat_times: np.ndarray,
        onset_times: np.ndarray,
        energy_data: dict,
        difficulty: float,
        total_duration: float,
    ) -> list[dict]:
        candidates = np.sort(np.union1d(beat_times, onset_times))
        energy_times = energy_data["times"]
        energy_values = energy_data["energy"]

        notes: list[dict] = []
        prev_lane = -1

        for i, t in enumerate(candidates):
            # Energy at current time
            idx = min(int(np.searchsorted(energy_times, t)), len(energy_values) - 1)
            e = float(energy_values[idx])

            # Density = difficulty scaled by local energy
            density = min(difficulty * (1.0 + e * 0.5), 1.0)
            if random.random() >= density:
                continue

            # How many simultaneous lanes (chord probability rises with difficulty)
            chord_prob = max(0.0, (difficulty - 0.5) * 0.8)
            n_lanes = 2 if (difficulty > 0.6 and random.random() < chord_prob) else 1

            lanes = self._pick_lanes(n_lanes, prev_lane)

            # Hold note: long gap to next candidate + probability weighted by difficulty & energy
            note_type = "single"
            hold_duration = 0.0
            if i < len(candidates) - 1:
                gap = float(candidates[i + 1]) - float(t)
                hold_prob = difficulty * 0.35 + e * 0.15
                if gap > self.HOLD_GAP_THRESHOLD and random.random() < hold_prob:
                    note_type = "hold"
                    hold_duration = round(gap * 0.8, 3)

            for lane in lanes:
                notes.append(
                    {
                        "time": round(float(t), 4),
                        "lane": lane,
                        "type": note_type,
                        "duration": hold_duration,
                    }
                )

            prev_lane = lanes[-1]

        return notes

    # ------------------------------------------------------------------ helpers

    def _pick_lanes(self, n: int, prev_lane: int) -> list[int]:
        pool = list(range(4))
        chosen: list[int] = []
        for _ in range(n):
            available = [l for l in pool if l not in chosen]
            # Avoid repeating the most recent lane for the first pick
            if len(chosen) == 0 and prev_lane in available and len(available) > 1:
                available = [l for l in available if l != prev_lane]
            chosen.append(random.choice(available))
        return chosen
