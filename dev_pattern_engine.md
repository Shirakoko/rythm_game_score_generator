# Pattern Engine 开发文档

## 一、问题诊断

当前 `NoteMapper.generate()` 的决策单元是**单个音符**：每个候选时间点独立决定是否放置、放在哪条轨道。结果是轨道序列在统计上接近均匀随机，缺乏人类谱师惯用的"段落感"。

人类谱师的实际思路：
> 选一个 pattern（如楼梯、交互）→ 连续打 4–8 个音符 → 切换下一个 pattern

---

## 二、目标架构

```
NoteMapper.generate()
    │
    ├─ 1. 密度筛选（保留现有逻辑）
    │       candidates → filtered_candidates
    │
    ├─ 2. 窗口分割（新增）
    │       filtered_candidates → windows[]  (每组 4–8 个时间点)
    │
    ├─ 3. 模式选择（新增）
    │       (difficulty, energy, prev_pattern) → PatternDef
    │
    ├─ 4. 模式应用（新增）
    │       (window, PatternDef) → notes[]
    │
    └─ 5. 长条注入（保留现有逻辑，在模式应用后叠加）
```

新增两个文件：
- `generators/pattern_library.py` — 模式定义库
- `generators/pattern_engine.py` — 窗口分割 + 模式选择 + 模式应用

修改一个文件：
- `generators/note_mapper.py` — 主流程改为调用 PatternEngine

---

## 三、数据结构

### 3.1 PatternDef

```python
@dataclass
class PatternDef:
    name: str
    category: str          # stream / stair / trill / jack / chord / hybrid / tech
    # 每个元素是该步骤要按下的轨道列表（单键用 [lane]，双押用 [l1, l2]）
    sequence: list[list[int]]
    min_difficulty: float  # 适用难度下限 [0, 1]
    max_difficulty: float  # 适用难度上限 [0, 1]
    min_energy: float      # 适用能量下限 [0, 1]
    max_energy: float      # 适用能量上限 [0, 1]
    weight: float = 1.0    # 基础选择权重
```

`sequence` 统一用 `list[list[int]]` 表示，单键 `[2]`，双押 `[1, 2]`，这样应用层不需要分支。

### 3.2 Window

```python
@dataclass
class Window:
    times: list[float]     # 该窗口内的候选时间点
    energy: float          # 窗口平均能量（用于模式选择）
```

---

## 四、模式库设计（pattern_library.py）

按文档中的十二类，精选适合程序生成的模式，每类至少覆盖低/中/高难度各一个变体。

### 示例条目

```python
PATTERNS: list[PatternDef] = [
    # ── Stream ──────────────────────────────────────────────
    PatternDef(
        name="straight_stream",
        category="stream",
        sequence=[[0],[1],[2],[3]],
        min_difficulty=0.2, max_difficulty=0.7,
        min_energy=0.3, max_energy=1.0,
        weight=1.2,
    ),
    PatternDef(
        name="reverse_stream",
        category="stream",
        sequence=[[3],[2],[1],[0]],
        min_difficulty=0.2, max_difficulty=0.7,
        min_energy=0.3, max_energy=1.0,
        weight=1.0,
    ),
    PatternDef(
        name="zigzag_stream",
        category="stream",
        sequence=[[0],[2],[1],[3]],
        min_difficulty=0.4, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.9,
    ),
    # ── Stair ───────────────────────────────────────────────
    PatternDef(
        name="stair_up",
        category="stair",
        sequence=[[0],[1],[2],[3]],
        min_difficulty=0.1, max_difficulty=0.5,
        min_energy=0.0, max_energy=0.7,
        weight=1.5,
    ),
    PatternDef(
        name="stair_down",
        category="stair",
        sequence=[[3],[2],[1],[0]],
        min_difficulty=0.1, max_difficulty=0.5,
        min_energy=0.0, max_energy=0.7,
        weight=1.5,
    ),
    PatternDef(
        name="stair_bidirectional",
        category="stair",
        sequence=[[0],[1],[2],[3],[2],[1]],
        min_difficulty=0.2, max_difficulty=0.6,
        min_energy=0.1, max_energy=0.8,
        weight=1.0,
    ),
    # ── Trill ───────────────────────────────────────────────
    PatternDef(
        name="inner_trill",
        category="trill",
        sequence=[[1],[2],[1],[2]],
        min_difficulty=0.3, max_difficulty=0.8,
        min_energy=0.3, max_energy=1.0,
        weight=1.0,
    ),
    PatternDef(
        name="outer_trill",
        category="trill",
        sequence=[[0],[3],[0],[3]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.8,
    ),
    PatternDef(
        name="offset_trill_24",
        category="trill",
        sequence=[[1],[3],[1],[3]],
        min_difficulty=0.4, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.9,
    ),
    # ── Jack ────────────────────────────────────────────────
    PatternDef(
        name="single_jack_col0",
        category="jack",
        sequence=[[0],[0],[0],[0]],
        min_difficulty=0.4, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.6,
    ),
    PatternDef(
        name="double_jack_01",
        category="jack",
        sequence=[[0],[0],[1],[1]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.7,
    ),
    # ── Chord ───────────────────────────────────────────────
    PatternDef(
        name="chord_roll",
        category="chord",
        sequence=[[0,1],[1,2],[2,3],[1,2]],
        min_difficulty=0.6, max_difficulty=1.0,
        min_energy=0.6, max_energy=1.0,
        weight=0.8,
    ),
    PatternDef(
        name="chord_alt",
        category="chord",
        sequence=[[0,1],[2,3],[0,1],[2,3]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.9,
    ),
    # ── Hybrid ──────────────────────────────────────────────
    PatternDef(
        name="jumpstream",
        category="hybrid",
        sequence=[[0,1],[2],[1,2],[3],[2,3]],
        min_difficulty=0.7, max_difficulty=1.0,
        min_energy=0.7, max_energy=1.0,
        weight=0.7,
    ),
    PatternDef(
        name="split_stream",
        category="hybrid",
        sequence=[[0],[2],[1],[3],[0],[2],[1],[3]],
        min_difficulty=0.5, max_difficulty=0.9,
        min_energy=0.4, max_energy=1.0,
        weight=0.8,
    ),
    # ── Tech ────────────────────────────────────────────────
    PatternDef(
        name="anti_stair",
        category="tech",
        sequence=[[0],[1],[3],[2],[1],[0],[2],[3]],
        min_difficulty=0.6, max_difficulty=1.0,
        min_energy=0.5, max_energy=1.0,
        weight=0.6,
    ),
    # ── Burst ───────────────────────────────────────────────
    PatternDef(
        name="short_burst",
        category="burst",
        sequence=[[0],[1],[2],[3],[1],[2]],
        min_difficulty=0.5, max_difficulty=1.0,
        min_energy=0.7, max_energy=1.0,
        weight=0.8,
    ),
]
```

> 后续可以继续扩充，每个 PatternDef 独立，不影响引擎逻辑。

---

## 五、PatternEngine 设计（pattern_engine.py）

### 5.1 窗口分割

```python
def split_into_windows(
    times: list[float],
    energy_at: Callable[[float], float],
    base_min: int = 4,
    base_max: int = 8,
) -> list[Window]:
```

**窗口大小策略：**
- 计算窗口起始时间点的平均能量 `e`
- `size = round(base_max - e * (base_max - base_min))`
  - 高能量 → 窗口小（4）→ 模式切换频繁，更有冲击感
  - 低能量 → 窗口大（8）→ 模式持续更长，更流畅
- 最后一个窗口不足 `base_min` 时，合并到前一个窗口

### 5.2 模式选择

```python
def select_pattern(
    difficulty: float,
    energy: float,
    prev_pattern: PatternDef | None,
    rng: random.Random,
) -> PatternDef:
```

**筛选逻辑（按顺序）：**
1. 过滤 `min_difficulty <= difficulty <= max_difficulty`
2. 过滤 `min_energy <= energy <= max_energy`
3. 若上一个模式存在，降低同类别模式的权重（×0.3），避免连续重复
4. 按 `weight` 加权随机选择

**兜底：** 若过滤后候选为空，放宽能量约束重新筛选；再空则返回 `stair_up`。

### 5.3 模式应用

```python
def apply_pattern(
    window: Window,
    pattern: PatternDef,
) -> list[dict]:
```

**应用逻辑：**
```
for i, t in enumerate(window.times):
    step = pattern.sequence[i % len(pattern.sequence)]
    for lane in step:
        emit note(time=t, lane=lane, type="single")
```

双押（`len(step) > 1`）时，同一时间点发出多个音符，这与现有 `chart_serializer` 的格式完全兼容。

### 5.4 过渡平滑（可选，第二期）

在两个窗口边界处，检查上一窗口末尾轨道与下一窗口首轨道的距离：
- 距离 > 2（如 0→3）且能量 < 0.5 时，将下一窗口的模式镜像（`lane = 3 - lane`）
- 这样可以避免低能量段出现突兀的大跨度跳

---

## 六、长条注入（保留现有逻辑）

长条（hold note）与 pattern 逻辑解耦，在 `apply_pattern` 之后单独处理：

```
for note in notes:
    if random.random() < hold_prob(difficulty, energy):
        note["type"] = "hold"
        note["duration"] = calc_duration(beat_interval, energy)
```

不改变轨道分配，只升级 note type。

---

## 七、note_mapper.py 改造

```python
class NoteMapper:
    def generate(self, beat_times, onset_times, energy_data, difficulty, total_duration):
        candidates = np.sort(np.union1d(beat_times, onset_times))
        energy_times = energy_data["times"]
        energy_values = energy_data["energy"]
        beat_interval = float(np.median(np.diff(beat_times))) if len(beat_times) > 1 else 0.5

        def energy_at(t):
            idx = min(int(np.searchsorted(energy_times, t)), len(energy_values) - 1)
            return float(energy_values[idx])

        # 1. 密度筛选（保留现有逻辑）
        filtered = [t for t in candidates if random.random() < min(difficulty * (1.0 + energy_at(t) * 0.5), 1.0)]

        # 2. 窗口分割
        windows = self.engine.split_into_windows(filtered, energy_at)

        # 3–4. 逐窗口选模式 + 应用
        notes = []
        prev_pattern = None
        for window in windows:
            pattern = self.engine.select_pattern(difficulty, window.energy, prev_pattern, self.rng)
            window_notes = self.engine.apply_pattern(window, pattern)
            prev_pattern = pattern
            notes.extend(window_notes)

        # 5. 长条注入
        notes = self._inject_holds(notes, difficulty, beat_interval, total_duration, energy_at)

        return notes
```

---

## 八、实现计划

| 步骤 | 文件 | 工作内容 |
|------|------|----------|
| 1 | `generators/pattern_library.py` | 新建，定义 `PatternDef` dataclass 和 `PATTERNS` 列表（覆盖全部十二类，约 20–30 条） |
| 2 | `generators/pattern_engine.py` | 新建，实现 `split_into_windows` / `select_pattern` / `apply_pattern` |
| 3 | `generators/note_mapper.py` | 重构主流程，调用 PatternEngine；`_pick_lanes` 可删除；`_inject_holds` 抽出为独立方法 |
| 4 | 测试 | 用现有音频跑一遍，对比改造前后的轨道序列分布，确认 pattern 段落可见 |

步骤 1 和 2 可以并行开发，步骤 3 依赖前两步完成。

---

## 九、预期效果

- 轨道序列从"均匀随机"变为"有段落的模式序列"
- 难度低时以楼梯/直线流为主，难度高时出现交互/双押/Tech
- 能量高峰处窗口变小、模式切换更频繁，形成"爆发感"
- 同类别模式不连续重复，保持谱面多样性
