import random
from dataclasses import dataclass
from typing import Callable

from .pattern_library import PatternDef, PATTERNS

_FALLBACK = next(p for p in PATTERNS if p.name == "stair_up")


@dataclass
class Window:
    times: list[float]
    energy: float


class PatternEngine:
    def split_into_windows(
        self,
        times: list[float],
        energy_at: Callable[[float], float],
        base_min: int = 4,
        base_max: int = 8,
    ) -> list[Window]:
        if not times:
            return []

        windows: list[Window] = []
        i = 0
        while i < len(times):
            e = energy_at(times[i])
            # High energy → smaller window; low energy → larger window
            size = round(base_max - e * (base_max - base_min))
            size = max(base_min, min(base_max, size))

            chunk = times[i : i + size]
            # Merge a trailing chunk that's too small into the previous window
            remaining = len(times) - (i + size)
            if remaining > 0 and remaining < base_min:
                chunk = times[i:]
                i = len(times)
            else:
                i += size

            avg_energy = sum(energy_at(t) for t in chunk) / len(chunk)
            windows.append(Window(times=chunk, energy=avg_energy))

        return windows

    def select_pattern(
        self,
        difficulty: float,
        energy: float,
        prev_pattern: PatternDef | None,
        rng: random.Random,
    ) -> PatternDef:
        candidates = self._filter(difficulty, energy)

        # Relax energy constraint if nothing matched
        if not candidates:
            candidates = self._filter(difficulty, energy, relax_energy=True)
        if not candidates:
            return _FALLBACK

        weights = []
        for p in candidates:
            w = p.weight
            # Penalise same category as previous to encourage variety
            if prev_pattern and p.category == prev_pattern.category:
                w *= 0.3
            weights.append(w)

        return rng.choices(candidates, weights=weights, k=1)[0]

    def apply_pattern(
        self,
        window: Window,
        pattern: PatternDef,
        rng: random.Random | None = None,
    ) -> list[dict]:
        seq = self._transform_sequence(pattern, rng or random.Random())
        notes: list[dict] = []
        for i, t in enumerate(window.times):
            step = seq[i % len(seq)]
            for lane in step:
                notes.append({"time": round(t, 4), "lane": lane, "type": "single", "duration": 0.0})
        return notes

    def _transform_sequence(
        self,
        pattern: PatternDef,
        rng: random.Random,
    ) -> list[list[int]]:
        seq = pattern.sequence

        # Jack / single-column patterns: pick a random target lane and shift all lanes
        # by the same offset so the pattern stays on one column.
        if pattern.category == "jack":
            all_lanes = {lane for step in seq for lane in step}
            if len(all_lanes) <= 2:
                min_lane = min(all_lanes)
                max_lane = max(all_lanes)
                span = max_lane - min_lane          # 0 for single-jack, 1 for double-jack
                max_offset = 3 - span
                offset = rng.randint(0, max_offset) - min_lane
                return [[lane + offset for lane in step] for step in seq]

        # All other patterns: 50 % chance of left-right mirror (lane → 3 - lane)
        if rng.random() < 0.5:
            return [[3 - lane for lane in step] for step in seq]

        return seq

    # ------------------------------------------------------------------ helpers

    def _filter(
        self,
        difficulty: float,
        energy: float,
        relax_energy: bool = False,
    ) -> list[PatternDef]:
        result = []
        for p in PATTERNS:
            if not (p.min_difficulty <= difficulty <= p.max_difficulty):
                continue
            if not relax_energy and not (p.min_energy <= energy <= p.max_energy):
                continue
            result.append(p)
        return result
