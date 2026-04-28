from dataclasses import dataclass, field


@dataclass
class PatternDef:
    name: str
    category: str
    # Each step is a list of lanes to press simultaneously (single=[lane], chord=[l1,l2])
    sequence: list[list[int]]
    min_difficulty: float
    max_difficulty: float
    min_energy: float
    max_energy: float
    weight: float = 1.0


PATTERNS: list[PatternDef] = [
    # ── Stream ──────────────────────────────────────────────────────────────
    PatternDef(
        name="straight_stream",
        category="stream",
        sequence=[[0], [1], [2], [3]],
        min_difficulty=0.2, max_difficulty=0.75,
        min_energy=0.3, max_energy=1.0,
        weight=1.2,
    ),
    PatternDef(
        name="reverse_stream",
        category="stream",
        sequence=[[3], [2], [1], [0]],
        min_difficulty=0.2, max_difficulty=0.75,
        min_energy=0.3, max_energy=1.0,
        weight=1.1,
    ),
    PatternDef(
        name="back_and_forth",
        category="stream",
        sequence=[[0], [1], [2], [1], [0], [1], [2], [1]],
        min_difficulty=0.3, max_difficulty=0.8,
        min_energy=0.3, max_energy=1.0,
        weight=0.9,
    ),
    PatternDef(
        name="zigzag_stream",
        category="stream",
        sequence=[[0], [2], [1], [3]],
        min_difficulty=0.4, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.9,
    ),
    PatternDef(
        name="shifted_stream",
        category="stream",
        sequence=[[1], [2], [3], [0]],
        min_difficulty=0.3, max_difficulty=0.8,
        min_energy=0.3, max_energy=1.0,
        weight=0.8,
    ),
    # ── Stair ───────────────────────────────────────────────────────────────
    PatternDef(
        name="stair_up",
        category="stair",
        sequence=[[0], [1], [2], [3]],
        min_difficulty=0.1, max_difficulty=0.55,
        min_energy=0.0, max_energy=0.75,
        weight=1.5,
    ),
    PatternDef(
        name="stair_down",
        category="stair",
        sequence=[[3], [2], [1], [0]],
        min_difficulty=0.1, max_difficulty=0.55,
        min_energy=0.0, max_energy=0.75,
        weight=1.5,
    ),
    PatternDef(
        name="stair_bidirectional",
        category="stair",
        sequence=[[0], [1], [2], [3], [2], [1]],
        min_difficulty=0.2, max_difficulty=0.65,
        min_energy=0.1, max_energy=0.8,
        weight=1.0,
    ),
    PatternDef(
        name="broken_stair",
        category="stair",
        sequence=[[0], [1], [3], [2]],
        min_difficulty=0.3, max_difficulty=0.7,
        min_energy=0.2, max_energy=0.85,
        weight=0.8,
    ),
    # ── Trill ───────────────────────────────────────────────────────────────
    PatternDef(
        name="inner_trill",
        category="trill",
        sequence=[[1], [2], [1], [2]],
        min_difficulty=0.3, max_difficulty=0.8,
        min_energy=0.3, max_energy=1.0,
        weight=1.0,
    ),
    PatternDef(
        name="outer_trill",
        category="trill",
        sequence=[[0], [3], [0], [3]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.8,
    ),
    PatternDef(
        name="offset_trill_13",
        category="trill",
        sequence=[[0], [2], [0], [2]],
        min_difficulty=0.4, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.9,
    ),
    PatternDef(
        name="offset_trill_24",
        category="trill",
        sequence=[[1], [3], [1], [3]],
        min_difficulty=0.4, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.9,
    ),
    # ── Jack ────────────────────────────────────────────────────────────────
    PatternDef(
        name="single_jack_col1",
        category="jack",
        sequence=[[0], [0], [0], [0]],
        min_difficulty=0.45, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.6,
    ),
    PatternDef(
        name="single_jack_col2",
        category="jack",
        sequence=[[1], [1], [1], [1]],
        min_difficulty=0.45, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.6,
    ),
    PatternDef(
        name="double_jack_01",
        category="jack",
        sequence=[[0], [0], [1], [1]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.7,
    ),
    PatternDef(
        name="double_jack_23",
        category="jack",
        sequence=[[2], [2], [3], [3]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.7,
    ),
    PatternDef(
        name="pseudo_trill_jack",
        category="jack",
        sequence=[[0], [1], [0], [0], [1], [0]],
        min_difficulty=0.55, max_difficulty=1.0,
        min_energy=0.55, max_energy=1.0,
        weight=0.65,
    ),
    # ── Chord ───────────────────────────────────────────────────────────────
    PatternDef(
        name="chord_roll",
        category="chord",
        sequence=[[0, 1], [1, 2], [2, 3], [1, 2]],
        min_difficulty=0.6, max_difficulty=1.0,
        min_energy=0.6, max_energy=1.0,
        weight=0.8,
    ),
    PatternDef(
        name="chord_alt_outer_inner",
        category="chord",
        sequence=[[0, 3], [1, 2], [0, 3], [1, 2]],
        min_difficulty=0.55, max_difficulty=1.0,
        min_energy=0.55, max_energy=1.0,
        weight=0.85,
    ),
    PatternDef(
        name="chord_alt_split",
        category="chord",
        sequence=[[0, 1], [2, 3], [0, 1], [2, 3]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.9,
    ),
    # ── Hybrid ──────────────────────────────────────────────────────────────
    PatternDef(
        name="jumpstream",
        category="hybrid",
        sequence=[[0, 1], [2], [1, 2], [3], [2, 3]],
        min_difficulty=0.7, max_difficulty=1.0,
        min_energy=0.7, max_energy=1.0,
        weight=0.7,
    ),
    PatternDef(
        name="split_stream",
        category="hybrid",
        sequence=[[0], [2], [1], [3], [0], [2], [1], [3]],
        min_difficulty=0.5, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.8,
    ),
    PatternDef(
        name="handstream",
        category="hybrid",
        sequence=[[0, 1, 2], [3], [1, 2, 3], [0]],
        min_difficulty=0.8, max_difficulty=1.0,
        min_energy=0.75, max_energy=1.0,
        weight=0.5,
    ),
    # ── Wide / Jump ──────────────────────────────────────────────────────────
    PatternDef(
        name="wide_jump",
        category="wide",
        sequence=[[0], [3], [1], [2], [0], [3]],
        min_difficulty=0.4, max_difficulty=0.85,
        min_energy=0.4, max_energy=1.0,
        weight=0.8,
    ),
    PatternDef(
        name="outer_reinforced",
        category="wide",
        sequence=[[0], [3], [0], [3], [1], [2]],
        min_difficulty=0.5, max_difficulty=0.9,
        min_energy=0.5, max_energy=1.0,
        weight=0.75,
    ),
    # ── Dense (small range) ──────────────────────────────────────────────────
    PatternDef(
        name="center_dense",
        category="dense",
        sequence=[[1], [2], [1], [2], [1], [2], [1], [2]],
        min_difficulty=0.3, max_difficulty=0.75,
        min_energy=0.4, max_energy=1.0,
        weight=0.85,
    ),
    # ── Wide Spread ──────────────────────────────────────────────────────────
    PatternDef(
        name="wide_spread",
        category="wide_spread",
        sequence=[[0], [3], [1], [2], [0], [3], [2], [1]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.7,
    ),
    # ── Tech ────────────────────────────────────────────────────────────────
    PatternDef(
        name="anti_stair",
        category="tech",
        sequence=[[0], [1], [3], [2], [1], [0], [2], [3]],
        min_difficulty=0.6, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.6,
    ),
    PatternDef(
        name="random_tech",
        category="tech",
        sequence=[[0], [2], [3], [1], [2], [0], [3], [1]],
        min_difficulty=0.65, max_difficulty=1.0,
        min_energy=0.55, max_energy=1.0,
        weight=0.55,
    ),
    PatternDef(
        name="hand_bias",
        category="tech",
        sequence=[[0], [1], [0], [1], [0], [2], [0], [1]],
        min_difficulty=0.5, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.65,
    ),
    # ── Burst ───────────────────────────────────────────────────────────────
    PatternDef(
        name="short_burst",
        category="burst",
        sequence=[[0], [1], [2], [3], [1], [2]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.7, max_energy=1.0,
        weight=0.8,
    ),
    PatternDef(
        name="chord_burst",
        category="burst",
        sequence=[[0, 1], [1, 2], [2, 3]],
        min_difficulty=0.65, max_difficulty=1.0,
        min_energy=0.75, max_energy=1.0,
        weight=0.75,
    ),
]
