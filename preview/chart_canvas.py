"""Falling-note chart preview rendered on a tk.Canvas.

Design decisions
----------------
* Two canvas layers distinguished by tags:
    "bg"   — static: lane backgrounds, dividers, judgement line, key zones.
              Redrawn only on resize (<Configure>).
    "note" — dynamic: note rectangles.
              Deleted and redrawn every frame (~60 fps via after(16, ...)).

* Time source is injected as get_time_fn: Callable[[], float] so the canvas
  is decoupled from AudioPlayer and can be tested independently.

* Fall-speed formula:
    y_of_note = judgement_y - (note_time - current_time) * fall_speed
  When (note_time - current_time) == 0 the note is exactly on the judgement line.
"""

import tkinter as tk
from typing import Callable

# ------------------------------------------------------------------ constants

LANE_COLORS = ["#ff6b6b", "#ffd93d", "#6bcbff", "#6bff9e"]
LANE_KEYS   = ["D", "F", "J", "K"]
_JUDGE_RATIO = 0.82     # judgement line at 82 % of canvas height
_NOTE_H      = 13       # half-height of a tap note (px)
_NOTE_PAD    = 5        # horizontal inset within lane (px)


def _darken(hex_color: str, factor: float = 0.35) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"


def _blend(hex_color: str, bg: str = "#1e1e2e", alpha: float = 0.4) -> str:
    """Linear blend of hex_color → bg (simulates transparency for hold body)."""
    def ch(h: str, i: int) -> int:
        return int(h[i * 2 + 1: i * 2 + 3], 16)

    r = int(ch(hex_color, 0) * alpha + ch(bg, 0) * (1 - alpha))
    g = int(ch(hex_color, 1) * alpha + ch(bg, 1) * (1 - alpha))
    b = int(ch(hex_color, 2) * alpha + ch(bg, 2) * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"


# ------------------------------------------------------------------ class

class ChartPreviewCanvas:
    """Embed this in any tk/CTk parent frame."""

    def __init__(self, parent, get_time_fn: Callable[[], float]) -> None:
        self._get_time = get_time_fn
        self._chart: dict | None = None
        self._fall_speed: float = 300.0   # px / second
        self._after_id: str | None = None
        self._running: bool = False

        self._canvas = tk.Canvas(parent, bg="#1e1e2e", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda _e: self._draw_background())

    # ------------------------------------------------------------------ API

    def set_fall_speed(self, speed: float) -> None:
        self._fall_speed = max(50.0, float(speed))

    def load_chart(self, chart: dict) -> None:
        self._chart = chart
        self._draw_background()
        if not self._running:
            self._running = True
            self._tick()

    def unload_chart(self) -> None:
        self._chart = None
        self._canvas.delete("note")
        self._draw_background()

    def start_animation(self) -> None:
        """Start the tick loop (canvas renders placeholder until chart is loaded)."""
        if not self._running:
            self._running = True
            self._tick()

    def stop_animation(self) -> None:
        self._running = False
        if self._after_id:
            try:
                self._canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    # ------------------------------------------------------------------ background (static)

    def _draw_background(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        self._canvas.delete("bg")
        self._canvas.delete("note")

        lw = w // 4          # lane width
        jy = h * _JUDGE_RATIO

        # ── Lane backgrounds (alternating shade) ─────────────────────────
        lane_fills = ["#1e1e2e", "#252538", "#1e1e2e", "#252538"]
        for i in range(4):
            x1 = i * lw
            x2 = (i + 1) * lw if i < 3 else w
            self._canvas.create_rectangle(
                x1, 0, x2, h, fill=lane_fills[i], outline="", tags="bg"
            )

        # ── Lane dividers ─────────────────────────────────────────────────
        for i in range(1, 4):
            x = i * lw
            self._canvas.create_line(x, 0, x, h, fill="#3a3a5c", width=1, tags="bg")

        # ── Judgement line (glow stack) ───────────────────────────────────
        self._canvas.create_line(0, jy + 4, w, jy + 4, fill="#2a2a44", width=6, tags="bg")
        self._canvas.create_line(0, jy + 2, w, jy + 2, fill="#555577", width=3, tags="bg")
        self._canvas.create_line(0, jy,     w, jy,     fill="#ddddff", width=2, tags="bg")

        # ── Key zones (below judgement line) ─────────────────────────────
        key_top = jy + 5
        key_bot = h - 5
        if key_bot > key_top + 6:
            for i, color in enumerate(LANE_COLORS):
                x1 = i * lw + 4
                x2 = (i + 1) * lw - 4 if i < 3 else w - 4
                self._canvas.create_rectangle(
                    x1, key_top, x2, key_bot,
                    fill=_darken(color, 0.28), outline=color, width=1, tags="bg"
                )
                self._canvas.create_text(
                    (x1 + x2) // 2, (key_top + key_bot) // 2,
                    text=LANE_KEYS[i], fill=color,
                    font=("Consolas", 11, "bold"), tags="bg"
                )

        # ── Lane name labels (top) ────────────────────────────────────────
        for i, color in enumerate(LANE_COLORS):
            cx = i * lw + lw // 2
            self._canvas.create_text(
                cx, 11, text=f"L{i + 1}",
                fill=color, font=("Consolas", 9), tags="bg"
            )

        # ── Placeholder text (shown when no chart is loaded) ──────────────
        if self._chart is None:
            mid_y = (jy - 24) / 2
            self._canvas.create_text(
                w // 2, mid_y - 14,
                text="暂无谱面",
                fill="#666688", font=("Arial", 15, "bold"), tags="bg"
            )
            self._canvas.create_text(
                w // 2, mid_y + 14,
                text="请先生成谱面，然后点击播放查看同步效果",
                fill="#4a4a6a", font=("Arial", 9), tags="bg"
            )

    # ------------------------------------------------------------------ animation tick

    def _tick(self) -> None:
        if not self._running:
            return
        try:
            if self._chart is not None:
                self._render_frame()
            self._after_id = self._canvas.after(16, self._tick)
        except tk.TclError:
            # Canvas was destroyed — stop silently
            self._running = False

    def _render_frame(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        self._canvas.delete("note")

        t_now = self._get_time()
        jy    = h * _JUDGE_RATIO
        lw    = w // 4
        # Seconds of chart visible above the judgement line
        visible_s = jy / self._fall_speed

        for event in self._chart["chartData"]:
            t_note = float(event["time"])
            dt     = t_note - t_now          # positive = upcoming, negative = past

            # Cull: skip if too far in future or just slipped past (allow 0.18 s tail)
            if dt > visible_s + 0.05 or dt < -0.18:
                continue

            # y-coordinate of the note's hit point (tracks the judgement line at dt=0)
            y_hit = jy - dt * self._fall_speed

            for lane_idx, track_val in enumerate(event["tracks"]):
                if track_val == "none":
                    continue

                x1 = lane_idx * lw + _NOTE_PAD
                x2 = (lane_idx + 1) * lw - _NOTE_PAD if lane_idx < 3 else w - _NOTE_PAD
                color = LANE_COLORS[lane_idx]

                if track_val == "single":
                    self._draw_tap(x1, x2, y_hit, color)
                elif track_val.startswith("hold_"):
                    hold_s = float(track_val[5:])
                    self._draw_hold(x1, x2, y_hit, hold_s * self._fall_speed, color)

    # ------------------------------------------------------------------ note drawing

    def _draw_tap(self, x1: float, x2: float, y: float, color: str) -> None:
        nh = _NOTE_H
        # Drop shadow
        self._canvas.create_rectangle(
            x1 + 2, y - nh + 2, x2 - 1, y + nh + 2,
            fill="#000000", outline="", tags="note"
        )
        # Main body
        self._canvas.create_rectangle(
            x1, y - nh, x2, y + nh,
            fill=color, outline="#ffffff", width=1, tags="note"
        )
        # Top highlight stripe
        self._canvas.create_rectangle(
            x1 + 2, y - nh, x2 - 2, y - nh + 4,
            fill="#ffffff", outline="", tags="note"
        )

    def _draw_hold(
        self, x1: float, x2: float, y_bottom: float, hold_px: float, color: str
    ) -> None:
        nh    = _NOTE_H
        y_top = y_bottom - hold_px

        # ── Hold body (semi-transparent via blended fill) ─────────────────
        body_color = _blend(color, alpha=0.45)
        if hold_px > nh:
            self._canvas.create_rectangle(
                x1 + 9, y_top + nh, x2 - 9, y_bottom,
                fill=body_color, outline="", tags="note"
            )
            # Side rails
            for rx in (x1 + 9, x2 - 9):
                self._canvas.create_line(
                    rx, y_top + nh, rx, y_bottom,
                    fill=color, width=1, tags="note"
                )

        # ── Top cap (start / press point) ────────────────────────────────
        self._canvas.create_rectangle(
            x1 + 2, y_top - nh, x2 - 2, y_top + nh + 2,
            fill="#000000", outline="", tags="note"   # shadow
        )
        self._canvas.create_rectangle(
            x1, y_top - nh, x2, y_top + nh,
            fill=color, outline="#ffffff", width=1, tags="note"
        )
        self._canvas.create_rectangle(
            x1 + 2, y_top - nh, x2 - 2, y_top - nh + 4,
            fill="#ffffff", outline="", tags="note"
        )

        # ── Bottom cap (release point) ────────────────────────────────────
        rh = max(6, nh // 2)
        self._canvas.create_rectangle(
            x1 + 4, y_bottom - rh, x2 - 4, y_bottom + rh,
            fill=_darken(color, 0.7), outline=color, width=1, tags="note"
        )
