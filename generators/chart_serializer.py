import json
from collections import defaultdict


class ChartSerializer:
    def build(
        self,
        notes: list[dict],
        song_name: str,
        total_duration: float,
        bpm: float,
        offset: float = 0.0,
    ) -> dict:
        # Group notes by timestamp → one chartData entry per beat-event
        groups: dict[float, list[dict]] = defaultdict(list)
        for note in notes:
            groups[note["time"]].append(note)

        chart_data = []
        for t in sorted(groups):
            tracks = ["none", "none", "none", "none"]
            for note in groups[t]:
                lane = note["lane"]
                if note["type"] == "hold":
                    tracks[lane] = f"hold_{note['duration']}"
                else:
                    tracks[lane] = "single"
            chart_data.append({"time": t, "tracks": tracks})

        return {
            "info": {
                "songName": song_name,
                "totalDuration": round(total_duration, 3),
                "bpm": round(bpm, 2),
                "offset": offset,
            },
            "chartData": chart_data,
        }

    def save(self, chart: dict, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chart, f, ensure_ascii=False, indent=2)
