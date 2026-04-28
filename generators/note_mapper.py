import bisect
import random
from collections import defaultdict

import numpy as np

from .pattern_engine import PatternEngine


class NoteMapper:
    def __init__(self):
        self._engine = PatternEngine()
        self._rng = random.Random()

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

        beat_interval = float(np.median(np.diff(beat_times))) if len(beat_times) > 1 else 0.5

        def energy_at(t: float) -> float:
            idx = min(int(np.searchsorted(energy_times, t)), len(energy_values) - 1)
            return float(energy_values[idx])

        # 1. Density filter
        filtered = [
            float(t)
            for t in candidates
            if self._rng.random() < min(difficulty * (1.0 + energy_at(float(t)) * 0.5), 1.0)
        ]

        if not filtered:
            return []

        # 2. Split into windows
        windows = self._engine.split_into_windows(filtered, energy_at)

        # 3–4. Select pattern per window and apply
        notes: list[dict] = []
        prev_pattern = None
        for window in windows:
            pattern = self._engine.select_pattern(difficulty, window.energy, prev_pattern, self._rng)
            notes.extend(self._engine.apply_pattern(window, pattern, self._rng))
            prev_pattern = pattern

        # 5. Inject hold notes
        notes = self._inject_holds(notes, difficulty, beat_interval, total_duration, energy_at)

        return notes

    # ------------------------------------------------------------------ helpers

    def _inject_holds(
        self,
        notes: list[dict],
        difficulty: float,
        beat_interval: float,
        total_duration: float,
        energy_at,
    ) -> list[dict]:
        notes.sort(key=lambda n: n["time"])

        lane_times: dict[int, list[float]] = defaultdict(list)
        for note in notes:
            lane_times[note["lane"]].append(note["time"])

        hold_end: dict[int, float] = {}

        for note in notes:
            lane = note["lane"]
            t = note["time"]
            e = energy_at(t)

            if hold_end.get(lane, 0.0) > t + 0.05:
                continue

            if self._rng.random() >= difficulty * 0.08 + e * 0.04:
                continue

            # Duration in beats (BPM-relative): low energy → shorter, high energy → longer
            max_beats = 2.0 + e * 2.0
            beats = self._rng.uniform(1.0, max_beats)
            dur = round(min(beat_interval * beats, total_duration - t - beat_interval), 3)

            # Cap so hold releases before next note on same lane (quarter-beat gap)
            times = lane_times[lane]
            pos = bisect.bisect_right(times, t)
            if pos < len(times):
                dur = round(min(dur, times[pos] - t - beat_interval * 0.25), 3)

            if dur < beat_interval * 0.5:
                continue

            note["type"] = "hold"
            note["duration"] = dur
            hold_end[lane] = t + dur

        return notes
