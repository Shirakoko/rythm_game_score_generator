"""Audio playback backend — wraps pygame.mixer with wall-clock position tracking.

Wall-clock approach:
    pygame.mixer.music.get_pos() resets to 0 after every seek/play call, making
    it useless for absolute position queries.  We instead record the wall time
    at which each play() / resume() call starts and compute:
        position = play_start_pos + (time.time() - wall_start)
"""

import os
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

import librosa


class AudioPlayer:
    """States: IDLE → READY ↔ PLAYING ↔ PAUSED → READY"""

    def __init__(self) -> None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self._ok = True
        except Exception as exc:
            print(f"[AudioPlayer] pygame.mixer init failed: {exc}")
            self._ok = False

        self._state: str = "IDLE"
        self._duration: float = 0.0
        self._wall_start: float = 0.0   # wall-clock time of last play/resume
        self._pos_start: float = 0.0    # audio position at last play/resume
        self._paused_pos: float = 0.0   # audio position when paused
        self._seek_pos: float = 0.0     # pending seek position (used in READY state)

    # ------------------------------------------------------------------ public

    def load(self, path: str) -> float:
        """Load audio file; returns total duration (seconds)."""
        if not self._ok:
            return 0.0
        self.stop()
        pygame.mixer.music.load(path)
        # librosa.get_duration(path=...) reads header without full decode
        self._duration = float(librosa.get_duration(path=path))
        self._seek_pos = 0.0
        self._state = "READY"
        return self._duration

    def play(self, start_pos: float | None = None) -> None:
        """Start playback from start_pos (defaults to current seek_pos)."""
        if not self._ok or self._state == "IDLE":
            return
        if start_pos is None:
            start_pos = self._seek_pos
        start_pos = _clamp(start_pos, 0.0, self._duration)
        pygame.mixer.music.play(0, start=start_pos)
        self._wall_start = time.time()
        self._pos_start = start_pos
        self._seek_pos = start_pos
        self._state = "PLAYING"

    def pause(self) -> None:
        if self._state != "PLAYING":
            return
        self._paused_pos = self.get_position()
        pygame.mixer.music.pause()
        self._state = "PAUSED"

    def resume(self) -> None:
        if self._state != "PAUSED":
            return
        pygame.mixer.music.unpause()
        self._wall_start = time.time()
        self._pos_start = self._paused_pos
        self._state = "PLAYING"

    def seek(self, pos: float) -> None:
        """Seek to pos (seconds).  Works in READY / PLAYING / PAUSED states."""
        if not self._ok or self._state == "IDLE":
            return
        pos = _clamp(pos, 0.0, self._duration)
        self._seek_pos = pos
        if self._state == "PLAYING":
            pygame.mixer.music.play(0, start=pos)
            self._wall_start = time.time()
            self._pos_start = pos
        elif self._state == "PAUSED":
            self._paused_pos = pos

    def stop(self) -> None:
        """Stop playback and reset position to 0."""
        if self._ok and self._state in ("PLAYING", "PAUSED"):
            pygame.mixer.music.stop()
        if self._state != "IDLE":
            self._state = "READY"
            self._pos_start = 0.0
            self._paused_pos = 0.0
            self._seek_pos = 0.0

    def get_position(self) -> float:
        """Return current playback position (seconds), thread-safe read."""
        if self._state == "PAUSED":
            return self._paused_pos
        if self._state == "PLAYING":
            elapsed = time.time() - self._wall_start
            return min(self._pos_start + elapsed, self._duration)
        # READY or IDLE: return pending seek position
        return self._seek_pos

    def quit(self) -> None:
        self.stop()
        if self._ok:
            pygame.mixer.quit()

    # ------------------------------------------------------------------ props

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def state(self) -> str:
        return self._state


# ------------------------------------------------------------------ helpers

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))
