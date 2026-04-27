"""4K 音游谱面生成器 — GUI 入口（进阶版）

新增功能
--------
* AudioPlayerBar  — 播放 / 暂停 / 停止 / ◀◀ 回首 + 可拖拽进度条
* ChartPreviewCanvas — 4 轨道实时下落预览，与音频严格同步
* 下落速度滑条 (100 ~ 800 px/s)

进度条防冲突
-----------
_user_dragging 标志：鼠标按下时暂停轮询写入，释放时执行 seek，避免
_poll_playback 与用户拖动互相干扰。
"""

import os
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from chart_generator import ChartGenerator
from audio_player import AudioPlayer
from preview.chart_canvas import ChartPreviewCanvas

# ------------------------------------------------------------------ theme

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ------------------------------------------------------------------ helpers

_DIFF_LABELS = [
    (0.00, 0.25, "简单"),
    (0.25, 0.55, "中等"),
    (0.55, 0.80, "困难"),
    (0.80, 1.01, "地狱"),
]


def _diff_label(v: float) -> str:
    for lo, hi, label in _DIFF_LABELS:
        if lo <= v < hi:
            return label
    return "地狱"


def _fmt(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


# ================================================================== App

class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("4K 音游谱面生成器")
        self.geometry("660x960")
        self.resizable(False, True)
        self.minsize(660, 780)

        self._generator = ChartGenerator()
        self._player    = AudioPlayer()

        self._audio_path: str | None = None
        self._chart:      dict | None = None

        # Seek-slider drag guard
        self._user_dragging: bool = False

        self._build_ui()

        # Start playback polling and canvas animation
        self._poll_playback()
        self._preview.start_animation()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ================================================================ UI build

    def _build_ui(self) -> None:

        # ── Title ────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="4K 音游谱面生成器",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(16, 8))

        # ── File selection ───────────────────────────────────────────────────
        f_file = ctk.CTkFrame(self)
        f_file.pack(fill="x", padx=24, pady=4)

        self._lbl_file = ctk.CTkLabel(f_file, text="未选择音频文件", anchor="w")
        self._lbl_file.pack(side="left", padx=12, pady=8, expand=True, fill="x")

        ctk.CTkButton(f_file, text="选择音频", width=110, command=self._browse).pack(
            side="right", padx=12, pady=8
        )

        # ── Audio player bar ─────────────────────────────────────────────────
        f_player = ctk.CTkFrame(self)
        f_player.pack(fill="x", padx=24, pady=4)

        # Row 1 — transport buttons + time label
        r1 = ctk.CTkFrame(f_player, fg_color="transparent")
        r1.pack(fill="x", padx=10, pady=(10, 4))

        self._btn_rewind = ctk.CTkButton(
            r1, text="◀◀", width=52, state="disabled", command=self._rewind
        )
        self._btn_rewind.pack(side="left", padx=(0, 4))

        self._btn_play = ctk.CTkButton(
            r1, text="▶  播放", width=100, state="disabled", command=self._toggle_play
        )
        self._btn_play.pack(side="left", padx=4)

        self._btn_stop = ctk.CTkButton(
            r1, text="■  停止", width=84, state="disabled", command=self._stop_audio
        )
        self._btn_stop.pack(side="left", padx=4)

        self._lbl_time = ctk.CTkLabel(r1, text="00:00 / 00:00", width=140, anchor="e")
        self._lbl_time.pack(side="right", padx=4)

        # Row 2 — seek slider
        r2 = ctk.CTkFrame(f_player, fg_color="transparent")
        r2.pack(fill="x", padx=10, pady=(0, 10))

        self._seek_var = ctk.DoubleVar(value=0.0)
        self._seek_slider = ctk.CTkSlider(
            r2, from_=0.0, to=1.0,
            variable=self._seek_var,
            state="disabled",
            command=self._on_slider_drag,
        )
        self._seek_slider.pack(fill="x")
        # Bind press/release on the internal widget (CTkSlider wraps a tk widget)
        self._seek_slider.bind("<ButtonPress-1>",
                               lambda _e: setattr(self, "_user_dragging", True))
        self._seek_slider.bind("<ButtonRelease-1>", self._on_seek_release)

        # ── Difficulty ───────────────────────────────────────────────────────
        f_diff = ctk.CTkFrame(self)
        f_diff.pack(fill="x", padx=24, pady=4)

        ctk.CTkLabel(f_diff, text="难度：", width=60).pack(side="left", padx=12, pady=8)

        self._diff_var = ctk.DoubleVar(value=0.5)
        ctk.CTkSlider(
            f_diff, from_=0.1, to=1.0,
            variable=self._diff_var, number_of_steps=18,
            command=self._on_diff_change,
        ).pack(side="left", padx=6, pady=8, expand=True, fill="x")

        self._lbl_diff = ctk.CTkLabel(f_diff, text="0.50 (中等)", width=120, anchor="w")
        self._lbl_diff.pack(side="right", padx=12, pady=8)

        # ── Offset ───────────────────────────────────────────────────────────
        f_off = ctk.CTkFrame(self)
        f_off.pack(fill="x", padx=24, pady=4)

        ctk.CTkLabel(f_off, text="偏移 (秒)：", width=80).pack(side="left", padx=12, pady=8)

        self._offset_entry = ctk.CTkEntry(f_off, width=90, placeholder_text="0.0")
        self._offset_entry.insert(0, "0.0")
        self._offset_entry.pack(side="left", padx=6, pady=8)

        # ── Generate / Export buttons ─────────────────────────────────────────
        f_btns = ctk.CTkFrame(self)
        f_btns.pack(fill="x", padx=24, pady=4)

        self._btn_gen = ctk.CTkButton(
            f_btns, text="生成谱面", state="disabled", command=self._generate
        )
        self._btn_gen.pack(side="left", padx=12, pady=8, expand=True, fill="x")

        self._btn_export = ctk.CTkButton(
            f_btns, text="导出 JSON", state="disabled", command=self._export
        )
        self._btn_export.pack(side="right", padx=12, pady=8, expand=True, fill="x")

        # ── Generation progress bar ───────────────────────────────────────────
        self._gen_bar = ctk.CTkProgressBar(self)
        self._gen_bar.pack(fill="x", padx=24, pady=(4, 2))
        self._gen_bar.set(0)

        # ── Log area (compact) ────────────────────────────────────────────────
        self._log = ctk.CTkTextbox(self, height=84, state="disabled", wrap="word")
        self._log.pack(fill="x", padx=24, pady=(2, 6))

        # ── Divider ───────────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=2, fg_color="#3a3a5c").pack(
            fill="x", padx=24, pady=6
        )

        # ── Fall-speed control ────────────────────────────────────────────────
        f_speed = ctk.CTkFrame(self)
        f_speed.pack(fill="x", padx=24, pady=4)

        ctk.CTkLabel(f_speed, text="下落速度：", width=80).pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(f_speed, text="慢", width=24).pack(side="left")

        self._speed_var = ctk.DoubleVar(value=300.0)
        ctk.CTkSlider(
            f_speed, from_=100, to=800,
            variable=self._speed_var, number_of_steps=35,
            command=self._on_speed_change,
        ).pack(side="left", padx=6, pady=8, expand=True, fill="x")

        ctk.CTkLabel(f_speed, text="快", width=24).pack(side="left")

        self._lbl_speed = ctk.CTkLabel(f_speed, text="300 px/s", width=84, anchor="w")
        self._lbl_speed.pack(side="right", padx=12, pady=8)

        # ── Preview canvas (takes all remaining vertical space) ───────────────
        f_canvas = ctk.CTkFrame(self, fg_color="#1e1e2e", corner_radius=8)
        f_canvas.pack(fill="both", padx=24, pady=(4, 16), expand=True)

        self._preview = ChartPreviewCanvas(
            parent=f_canvas,
            get_time_fn=self._player.get_position,
        )

    # ================================================================ playback polling

    def _poll_playback(self) -> None:
        """Called every 100 ms from the main thread to sync UI to AudioPlayer."""
        dur = self._player.duration
        state = self._player.state

        if state in ("PLAYING", "PAUSED") and dur > 0:
            pos = self._player.get_position()

            # Update seek slider (skip if user is dragging)
            if not self._user_dragging:
                self._seek_var.set(pos / dur)

            self._lbl_time.configure(text=f"{_fmt(pos)} / {_fmt(dur)}")

            # Auto-stop when playback reaches the end
            if state == "PLAYING" and pos >= dur:
                self._player.stop()
                self._seek_var.set(1.0)
                self._btn_play.configure(text="▶  播放")

        self.after(100, self._poll_playback)

    # ================================================================ player callbacks

    def _toggle_play(self) -> None:
        state = self._player.state
        if state == "READY":
            self._player.play()
            self._btn_play.configure(text="⏸  暂停")
        elif state == "PLAYING":
            self._player.pause()
            self._btn_play.configure(text="▶  播放")
        elif state == "PAUSED":
            self._player.resume()
            self._btn_play.configure(text="⏸  暂停")

    def _stop_audio(self) -> None:
        self._player.stop()
        self._seek_var.set(0.0)
        self._btn_play.configure(text="▶  播放")
        dur = self._player.duration
        self._lbl_time.configure(text=f"00:00 / {_fmt(dur)}")

    def _rewind(self) -> None:
        self._player.seek(0.0)
        self._seek_var.set(0.0)

    def _on_slider_drag(self, val: float) -> None:
        """Called continuously while slider moves — only update time label."""
        dur = self._player.duration
        if dur > 0:
            self._lbl_time.configure(text=f"{_fmt(float(val) * dur)} / {_fmt(dur)}")

    def _on_seek_release(self, _event) -> None:
        self._user_dragging = False
        dur = self._player.duration
        if dur > 0:
            self._player.seek(self._seek_var.get() * dur)

    # ================================================================ chart callbacks

    def _on_diff_change(self, val: float) -> None:
        v = float(val)
        self._lbl_diff.configure(text=f"{v:.2f} ({_diff_label(v)})")

    def _on_speed_change(self, val: float) -> None:
        speed = float(val)
        self._lbl_speed.configure(text=f"{speed:.0f} px/s")
        self._preview.set_fall_speed(speed)

    # ================================================================ file / generate / export

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[
                ("音频文件", "*.mp3 *.wav *.ogg *.flac *.aac *.m4a"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return

        self._audio_path = path
        self._lbl_file.configure(text=os.path.basename(path))

        # Reset chart state
        self._chart = None
        self._btn_export.configure(state="disabled")
        self._preview.unload_chart()

        self._btn_gen.configure(state="normal")
        self._log_write(f"已选择：{os.path.basename(path)}")

        # Load audio into player (fast: reads header only for duration)
        try:
            dur = self._player.load(path)
            self._lbl_time.configure(text=f"00:00 / {_fmt(dur)}")
            self._seek_var.set(0.0)
            for w in (self._seek_slider, self._btn_rewind,
                      self._btn_play, self._btn_stop):
                w.configure(state="normal")
            self._btn_play.configure(text="▶  播放")
            self._log_write(f"音频加载完成，时长 {_fmt(dur)}")
        except Exception as exc:
            self._log_write(f"[警告] 音频加载失败：{exc}")

    def _generate(self) -> None:
        if not self._audio_path:
            return

        difficulty = self._diff_var.get()
        try:
            offset = float(self._offset_entry.get())
        except ValueError:
            offset = 0.0

        self._btn_gen.configure(state="disabled")
        self._btn_export.configure(state="disabled")
        self._gen_bar.set(0)
        self._chart = None
        self._preview.unload_chart()

        _STEPS = [
            "正在加载音频...",
            "正在分析节拍和 BPM...",
            "正在分析能量曲线...",
            "正在分析音乐结构...",
            "正在生成谱面音符...",
        ]
        _step_idx = [0]

        def on_progress(msg: str) -> None:
            def _ui() -> None:
                self._log_write(msg)
                if msg in _STEPS:
                    _step_idx[0] += 1
                    self._gen_bar.set(_step_idx[0] / len(_STEPS))
            self.after(0, _ui)

        def worker() -> None:
            try:
                chart = self._generator.generate(
                    audio_path=self._audio_path,
                    difficulty=difficulty,
                    offset=offset,
                    on_progress=on_progress,
                )

                def _done() -> None:
                    self._chart = chart
                    self._gen_bar.set(1.0)
                    self._btn_gen.configure(state="normal")
                    self._btn_export.configure(state="normal")
                    self._preview.load_chart(chart)
                    self._log_write(
                        f"谱面已加载到预览 — 共 {len(chart['chartData'])} 个事件，"
                        "点击播放查看同步效果"
                    )

                self.after(0, _done)

            except Exception as exc:
                def _err() -> None:
                    self._log_write(f"[错误] {exc}")
                    self._btn_gen.configure(state="normal")
                    self._gen_bar.set(0)

                self.after(0, _err)

        threading.Thread(target=worker, daemon=True).start()

    def _export(self) -> None:
        if not self._chart:
            return
        default_name = self._chart["info"]["songName"] + ".json"
        path = filedialog.asksaveasfilename(
            title="保存谱面文件",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self._generator.save(self._chart, path)
        self._log_write(f"已导出：{os.path.basename(path)}")
        messagebox.showinfo("导出成功", f"谱面已保存到：\n{path}")

    # ================================================================ utils

    def _log_write(self, msg: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _on_close(self) -> None:
        self._preview.stop_animation()
        self._player.quit()
        self.destroy()


# ================================================================== entry

if __name__ == "__main__":
    app = App()
    app.mainloop()
