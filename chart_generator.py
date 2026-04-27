import os
from typing import Callable

import librosa

from analyzers.beat_analyzer import BeatAnalyzer
from analyzers.energy_analyzer import EnergyAnalyzer
from analyzers.structure_analyzer import StructureAnalyzer
from generators.note_mapper import NoteMapper
from generators.chart_serializer import ChartSerializer


class ChartGenerator:
    def __init__(self) -> None:
        self._beat = BeatAnalyzer()
        self._energy = EnergyAnalyzer()
        self._structure = StructureAnalyzer()
        self._mapper = NoteMapper()
        self._serializer = ChartSerializer()

    def generate(
        self,
        audio_path: str,
        difficulty: float = 0.5,
        offset: float = 0.0,
        on_progress: Callable[[str], None] | None = None,
    ) -> dict:
        def log(msg: str) -> None:
            if on_progress:
                on_progress(msg)

        log("正在加载音频...")
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        total_duration = librosa.get_duration(y=y, sr=sr)

        log("正在分析节拍和 BPM...")
        beat_data = self._beat.analyze(y, sr)

        log("正在分析能量曲线...")
        energy_data = self._energy.analyze(y, sr)

        log("正在分析音乐结构...")
        segments = self._structure.analyze(energy_data)

        log(
            f"BPM: {beat_data['tempo']:.1f}  |  时长: {total_duration:.1f}s  |  "
            f"Onset 点: {len(beat_data['onset_times'])}  |  段落: {len(segments)}"
        )

        log("正在生成谱面音符...")
        notes = self._mapper.generate(
            beat_times=beat_data["beat_times"],
            onset_times=beat_data["onset_times"],
            energy_data=energy_data,
            difficulty=difficulty,
            total_duration=total_duration,
        )

        song_name = os.path.splitext(os.path.basename(audio_path))[0]
        chart = self._serializer.build(
            notes=notes,
            song_name=song_name,
            total_duration=total_duration,
            bpm=beat_data["tempo"],
            offset=offset,
        )

        log(f"生成完成！共 {len(chart['chartData'])} 个音符事件")
        return chart

    def save(self, chart: dict, output_path: str) -> None:
        self._serializer.save(chart, output_path)
