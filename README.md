# 4K 音游谱面生成器

一个基于音频分析的 4K 下落式音游谱面自动生成工具。导入 MP3，设定难度，一键生成可供游戏引擎直接读取的 JSON 谱面，并在内置预览窗口中实时校验效果。

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 功能一览

| 功能 | 说明 |
|------|------|
| **自动 BPM 检测** | 使用 `librosa.beat.beat_track` 分析节奏 |
| **Onset 打击点检测** | 提取音乐中每个可打点作为音符候选 |
| **能量曲线分析** | 归一化 RMS + 滑动平均，动态调整音符密度 |
| **段落划分** | 基于能量自动识别主歌 / 副歌 / 静音段 |
| **难度系统** | 0.1 ~ 1.0 连续参数，影响密度、同时键、长按比例 |
| **音频播放** | 内置播放器，支持播放 / 暂停 / 停止 / 拖拽进度条 |
| **谱面预览** | 4 轨道实时下落动画，与音频严格同步，可调节下落速度 |
| **导出 JSON** | 输出符合规范的谱面数据结构 |

---

## 快速开始

### 环境要求

- Python 3.11 或更高版本
- Windows 10 / 11（macOS / Linux 未测试，理论可用）

### 安装依赖

```bash
pip install librosa numpy customtkinter soundfile pydub scipy pygame
```

### 运行

```bash
python main.py
```

---

## 使用流程

```
1. 点击「选择音频」  →  导入 MP3 / WAV / OGG / FLAC 文件
2. 拖动「难度」滑条  →  选择 简单 / 中等 / 困难 / 地狱
3. 点击「生成谱面」  →  等待分析完成（进度条 + 日志）
4. 点击「▶ 播放」   →  在预览窗口中查看音符下落效果
5. 调节「下落速度」  →  100 ~ 800 px/s，验证视觉体验
6. 点击「导出 JSON」 →  保存谱面文件
```

> **提示**：可以先导入音频试听，再点「生成谱面」；谱面生成完后会自动加载到预览窗口。

---

## 谱面数据结构

导出的 JSON 文件格式如下：

```json
{
  "info": {
    "songName": "example",
    "totalDuration": 183.5,
    "bpm": 128.0,
    "offset": 0.0
  },
  "chartData": [
    {
      "time": 0.234,
      "tracks": ["single", "none", "none", "none"]
    },
    {
      "time": 0.703,
      "tracks": ["none", "hold_0.48", "none", "single"]
    },
    {
      "time": 1.172,
      "tracks": ["none", "none", "single", "none"]
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `info.songName` | string | 曲名（取自文件名） |
| `info.totalDuration` | float | 音频总时长（秒） |
| `info.bpm` | float | 检测到的 BPM |
| `info.offset` | float | 谱面偏移量（秒） |
| `chartData[].time` | float | 该拍事件的绝对时间（秒） |
| `chartData[].tracks` | array[4] | 4 条轨道的音符类型 |

### tracks 取值

| 值 | 含义 |
|----|------|
| `"none"` | 该轨道无音符 |
| `"single"` | 单点音符（Tap） |
| `"hold_X.XX"` | 长按音符，持续 X.XX 秒 |

---

## 难度系统

| 滑条值 | 标签 | 效果 |
|--------|------|------|
| 0.1 ~ 0.24 | 简单 | 稀疏单点，无连打，长按极少 |
| 0.25 ~ 0.54 | 中等 | 中密度，偶有双键 |
| 0.55 ~ 0.79 | 困难 | 高密度，双键多，长按增多 |
| 0.80 ~ 1.0 | 地狱 | 极密，频繁双键，大量长按 |

音符密度公式：`density = difficulty × (1 + local_energy × 0.5)`，高潮段自动加密。

---

## 项目结构

```
rythm_game_score_generator/
│
├── main.py                    # GUI 入口（customtkinter）
├── chart_generator.py         # 主控制器，串联各分析 / 生成模块
├── audio_player.py            # 音频播放后端（pygame.mixer + wall-clock 计时）
│
├── analyzers/
│   ├── beat_analyzer.py       # BPM + 节拍 + Onset 检测（librosa）
│   ├── energy_analyzer.py     # RMS 能量归一化与平滑
│   └── structure_analyzer.py  # 基于能量的段落分类
│
├── generators/
│   ├── note_mapper.py         # 音符生成（密度、轨道分配、长按逻辑）
│   └── chart_serializer.py    # 序列化为规范 JSON 结构
│
├── preview/
│   └── chart_canvas.py        # 4 轨道下落动画（tk.Canvas，60 fps）
│
├── .vscode/
│   └── launch.json            # VSCode 调试配置（3 个配置项）
│
├── 开发文档.md
└── 进阶功能开发文档.md
```

---

## 依赖清单

| 库 | 版本 | 用途 |
|----|------|------|
| `librosa` | 0.11.0 | 音频分析（BPM、Onset、RMS、时长读取） |
| `numpy` | 2.3.4 | 数值计算 |
| `scipy` | 1.17.1 | 信号处理辅助 |
| `customtkinter` | 5.2.2 | 现代风格 GUI |
| `pygame` | 2.6.1 | 音频播放（mixer） |
| `soundfile` | 0.13.1 | 音频文件 I/O |
| `pydub` | 0.25.1 | 音频格式处理 |

---

## VSCode 调试

打开项目文件夹后，按 `F5` 选择以下配置之一：

| 配置名 | 说明 |
|--------|------|
| 运行谱面生成器 | 正常启动，断点只进入自己的代码 |
| 调试谱面生成器（含库内部） | `justMyCode=false`，可单步进入 librosa / pygame |
| 调试 ChartGenerator（无 GUI） | 单独调试核心逻辑，适合在 `chart_generator.py` 底部写测试块 |

---

## 已知限制

- MP3 格式在 Windows 上依赖 Windows Media Foundation 解码，通常无需额外安装；Linux 上需要 `ffmpeg` 或 `gstreamer`。
- `librosa.get_duration(path=...)` 对 VBR 编码的 MP3 可能略有误差（< 1 秒）。
- 谱面生成有一定随机性，相同参数每次结果不完全一致（`random.random()` 控制密度采样）；如需复现，可在 `note_mapper.py` 中固定 `random.seed()`。

---

## License

MIT
