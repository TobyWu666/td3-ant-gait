"""Build non-web TensorBoard analysis artifacts for the RLAP TD3 project.

The local Python environment used for the report does not include TensorBoard,
so this script implements the small subset of TFRecord/protobuf parsing needed
to extract scalar summaries from TensorBoard event files.
"""
from __future__ import annotations

import csv
import math
import os
import struct
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/rlap_matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/private/tmp/rlap_xdg_cache")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "RLAP_TD3_TB_analysis"
FIGS = OUTPUT / "figures"
DATA = OUTPUT / "data"

DT = 0.05


EVENT_RUNS = {
    "Alpha": [
        ROOT / "RL_Labcowork/output/02train_td3/tb/events.out.tfevents.1781860712.AndrewdeMacBook-Air.local.81762.0",
        ROOT / "RL_Labcowork/output/02train_td3/tb/events.out.tfevents.1781945677.AndrewdeMacBook-Air.local.88916.0",
    ],
    "Beta": [
        ROOT / "RL_Labcowork/output/03train_td3/tb/TD3_1/events.out.tfevents.1782023819.AndrewdeMacBook-Air.local.96436.0",
    ],
    "Gamma-04": [
        ROOT / "RL_Labcowork/output/04train_td3/tb/TD3_1/events.out.tfevents.1782057248.aitopatom-186a.1155707.0",
    ],
    "Gamma-06": [
        ROOT / "RL_Labcowork/output/06train_td3/tb/TD3_1/events.out.tfevents.1782071002.aitopatom-186a.1452301.0",
    ],
    "Gamma-07": [
        ROOT / "RL_Labcowork/output/07train_td3/tb/TD3_1/events.out.tfevents.1782106375.aitopatom-186a.1660807.0",
    ],
    "Gamma-08": [
        ROOT / "RL_Labcowork/output/08train_td3/tb/TD3_1/events.out.tfevents.1782111576.aitopatom-186a.1771772.0",
    ],
    "BetaPrime": [
        ROOT / "RL_Labcowork/output/12train_td3/tb/TD3_1/events.out.tfevents.1782125847.aitopatom-186a.2011825.0",
    ],
    "Theta-15A": [
        ROOT / "RL_Labcowork/output/15A/seed_1_fw18/tb/TD3_1/events.out.tfevents.1782200184.aitopatom-186a.3057201.0",
    ],
}


FINAL_SCORECARD = [
    dict(model="Beta", role="natural baseline", ep_len=1000, mean_speed=0.940, speed_error=0.140,
         regularity=0.239, anti_phase=0.209, diagonal_sync=0.712, jerk=0.028, cot=1.02,
         uprightness=0.986),
    dict(model="Gamma-04", role="stable progress base", ep_len=1000, mean_speed=1.290, speed_error=0.328,
         regularity=0.334, anti_phase=0.321, diagonal_sync=0.601, jerk=0.329, cot=5.56,
         uprightness=0.982),
    dict(model="Gamma-05", role="gait/posture fusion", ep_len=1000, mean_speed=1.370, speed_error=0.397,
         regularity=0.355, anti_phase=0.326, diagonal_sync=0.677, jerk=0.158, cot=2.85,
         uprightness=0.977),
    dict(model="Gamma-06", role="tent speed + smooth", ep_len=1000, mean_speed=0.830, speed_error=0.219,
         regularity=0.344, anti_phase=0.212, diagonal_sync=0.552, jerk=0.087, cot=2.62,
         uprightness=0.989),
    dict(model="Gamma-07", role="speed balanced", ep_len=1000, mean_speed=0.958, speed_error=0.100,
         regularity=0.308, anti_phase=0.267, diagonal_sync=0.544, jerk=0.120, cot=3.01,
         uprightness=0.979),
    dict(model="Gamma-08", role="proxy winner", ep_len=1000, mean_speed=0.922, speed_error=0.168,
         regularity=0.380, anti_phase=0.358, diagonal_sync=0.575, jerk=0.133, cot=4.16,
         uprightness=0.993),
    dict(model="BetaPrime-25k", role="best checkpoint", ep_len=1000, mean_speed=0.983, speed_error=0.108,
         regularity=float("nan"), anti_phase=0.245, diagonal_sync=0.678, jerk=0.037, cot=0.960,
         uprightness=0.990),
    dict(model="Theta-15A", role="theta final", ep_len=1000, mean_speed=0.913, speed_error=0.122,
         regularity=float("nan"), anti_phase=float("nan"), diagonal_sync=0.744, jerk=0.052, cot=1.62,
         uprightness=0.991),
]


SELECTED_CSV_TAGS = {
    "Eval/reward",
    "Train/reward",
    "eval/episode_return",
    "eval/episode_length",
    "eval/speed_error",
    "eval/distance",
    "eval/action_jerk",
    "eval/transport_cost",
    "eval/contact_regularity",
    "eval/diagonal_sync",
    "eval/anti_phase",
    "eval/uprightness",
    "gait/x_velocity",
    "contacts/diagonal_sync",
}


PALETTE = {
    "Alpha": "#7a8890",
    "Beta": "#315d6a",
    "Gamma-04": "#9f7056",
    "Gamma-05": "#b9894a",
    "Gamma-06": "#6f8f72",
    "Gamma-07": "#2f8f4e",
    "Gamma-08": "#4f7ca9",
    "BetaPrime": "#bd5b47",
    "BetaPrime-25k": "#bd5b47",
    "Theta-15A": "#2d4f9d",
}


def read_varint(buf: bytes, i: int) -> tuple[int, int]:
    shift = 0
    value = 0
    while True:
        b = buf[i]
        i += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, i
        shift += 7


def parse_fields(buf: bytes):
    i = 0
    n = len(buf)
    while i < n:
        key, i = read_varint(buf, i)
        field = key >> 3
        wire = key & 0x07
        if wire == 0:
            value, i = read_varint(buf, i)
            yield field, wire, value
        elif wire == 1:
            value = buf[i:i + 8]
            i += 8
            yield field, wire, value
        elif wire == 2:
            length, i = read_varint(buf, i)
            value = buf[i:i + length]
            i += length
            yield field, wire, value
        elif wire == 5:
            value = buf[i:i + 4]
            i += 4
            yield field, wire, value
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire}")


def read_tfrecord(path: Path):
    with path.open("rb") as fh:
        while True:
            header = fh.read(8)
            if not header:
                break
            if len(header) != 8:
                break
            length = struct.unpack("<Q", header)[0]
            fh.read(4)
            data = fh.read(length)
            fh.read(4)
            if len(data) == length:
                yield data


def scalar_from_tensor(tensor: bytes) -> float | None:
    dtype = None
    content = None
    float_vals = []
    double_vals = []
    for field, wire, value in parse_fields(tensor):
        if field == 1 and wire == 0:
            dtype = value
        elif field == 4 and wire == 2:
            content = value
        elif field == 5:
            if wire == 5:
                float_vals.append(struct.unpack("<f", value)[0])
            elif wire == 2:
                float_vals.extend(struct.unpack("<" + "f" * (len(value) // 4), value))
        elif field == 6:
            if wire == 1:
                double_vals.append(struct.unpack("<d", value)[0])
            elif wire == 2:
                double_vals.extend(struct.unpack("<" + "d" * (len(value) // 8), value))
    if content:
        if dtype == 1 and len(content) >= 4:
            return float(struct.unpack("<f", content[:4])[0])
        if dtype == 2 and len(content) >= 8:
            return float(struct.unpack("<d", content[:8])[0])
        if len(content) == 4:
            return float(struct.unpack("<f", content)[0])
        if len(content) == 8:
            return float(struct.unpack("<d", content)[0])
    if float_vals:
        return float(float_vals[0])
    if double_vals:
        return float(double_vals[0])
    return None


def parse_summary(summary: bytes) -> list[tuple[str, float]]:
    rows = []
    for field, wire, value in parse_fields(summary):
        if field != 1 or wire != 2:
            continue
        tag = None
        scalar = None
        for vf, vw, vv in parse_fields(value):
            if vf == 1 and vw == 2:
                tag = vv.decode("utf-8", errors="replace")
            elif vf == 2 and vw == 5:
                scalar = float(struct.unpack("<f", vv)[0])
            elif vf == 8 and vw == 2:
                scalar = scalar_from_tensor(vv)
        if tag is not None and scalar is not None and math.isfinite(scalar):
            rows.append((tag, scalar))
    return rows


def parse_event_scalars(path: Path) -> list[dict]:
    rows = []
    for record in read_tfrecord(path):
        step = None
        wall_time = None
        summaries = []
        for field, wire, value in parse_fields(record):
            if field == 1 and wire == 1:
                wall_time = struct.unpack("<d", value)[0]
            elif field == 2 and wire == 0:
                step = int(value)
            elif field == 5 and wire == 2:
                summaries = parse_summary(value)
        if step is None:
            continue
        for tag, scalar in summaries:
            rows.append(dict(step=step, wall_time=wall_time or 0.0, tag=tag, value=scalar))
    return rows


def extract_all() -> list[dict]:
    all_rows = []
    for model, paths in EVENT_RUNS.items():
        for path in paths:
            if not path.exists():
                continue
            for row in parse_event_scalars(path):
                row["model"] = model
                row["source"] = str(path.relative_to(ROOT))
                all_rows.append(row)
    all_rows.sort(key=lambda r: (r["model"], r["tag"], r["step"], r["wall_time"]))
    return all_rows


def write_csv(rows: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    compact_rows = []
    for row in rows:
        if row["tag"] not in SELECTED_CSV_TAGS:
            continue
        # Per-step Beta training diagnostics are useful for context but too dense
        # for handoff. Keep only a thin sample; eval curves are already sparse.
        if row["tag"].startswith(("gait/", "contacts/")) and row["step"] % 5000 != 0:
            continue
        compact_rows.append(row)

    with (DATA / "tb_selected_scalars.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["model", "tag", "step", "value", "wall_time", "source"])
        writer.writeheader()
        writer.writerows(compact_rows)

    fieldnames = ["model", "role", "ep_len", "mean_speed", "speed_error", "regularity",
                  "anti_phase", "diagonal_sync", "jerk", "cot", "uprightness"]
    with (DATA / "final_scorecard.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(FINAL_SCORECARD)


def by_model_tag(rows: list[dict]) -> dict[str, dict[str, list[tuple[int, float]]]]:
    out: dict[str, dict[str, list[tuple[int, float]]]] = defaultdict(lambda: defaultdict(list))
    seen = set()
    for row in rows:
        key = (row["model"], row["tag"], row["step"], row["value"])
        if key in seen:
            continue
        seen.add(key)
        out[row["model"]][row["tag"]].append((int(row["step"]), float(row["value"])))
    return out


def mean_speed_series(tags: dict[str, list[tuple[int, float]]]) -> list[tuple[int, float]]:
    distances = dict(tags.get("eval/distance", []))
    lengths = dict(tags.get("eval/episode_length", []))
    series = []
    for step in sorted(set(distances) & set(lengths)):
        if lengths[step] > 0:
            series.append((step, distances[step] / (lengths[step] * DT)))
    return series


def style_ax(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=8)
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#ddd7c8", linewidth=0.7, alpha=0.75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#c9c2b6")
    ax.spines["bottom"].set_color("#c9c2b6")
    ax.tick_params(colors="#33433d", labelsize=9)


def savefig(name: str) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGS / name, dpi=180, bbox_inches="tight")
    plt.close()


def plot_training_curves(grouped: dict[str, dict[str, list[tuple[int, float]]]]) -> None:
    metrics = [
        ("eval/episode_length", "Survival: episode length", "steps"),
        ("mean_speed", "Speed from TB distance", "m/s"),
        ("eval/speed_error", "Speed error", "abs error"),
        ("eval/action_jerk", "Action jerk", "lower is smoother"),
        ("eval/transport_cost", "Cost of transport", "lower is better"),
        ("eval/diagonal_sync", "Diagonal sync", "higher is better"),
    ]
    models = ["Gamma-04", "Gamma-06", "Gamma-07", "Gamma-08", "BetaPrime", "Theta-15A"]
    fig, axes = plt.subplots(3, 2, figsize=(13, 11))
    fig.suptitle("TensorBoard evaluation curves by model branch", fontsize=18, fontweight="bold", x=0.02, ha="left")
    for ax, (tag, title, ylabel) in zip(axes.ravel(), metrics):
        for model in models:
            tags = grouped.get(model, {})
            series = mean_speed_series(tags) if tag == "mean_speed" else tags.get(tag, [])
            if not series:
                continue
            xs = [x / 1000 for x, _ in series]
            ys = [y for _, y in series]
            ax.plot(xs, ys, label=model, color=PALETTE.get(model, "#444"), linewidth=2)
        if tag == "mean_speed":
            ax.axhline(1.0, color="#8a9690", linestyle="--", linewidth=1)
        if tag == "eval/episode_length":
            ax.axhline(1000, color="#8a9690", linestyle="--", linewidth=1)
        style_ax(ax, title, ylabel)
        ax.set_xlabel("training steps (k)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    savefig("tb_evaluation_curves.png")


def plot_final_scorecard() -> None:
    models = [r["model"] for r in FINAL_SCORECARD]
    metrics = [
        ("mean_speed", "Mean speed", "target=1.0"),
        ("speed_error", "Speed error", "lower"),
        ("jerk", "Action jerk", "lower"),
        ("cot", "CoT", "lower"),
        ("diagonal_sync", "Diagonal sync", "higher"),
        ("uprightness", "Uprightness", "higher"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.2))
    fig.suptitle("Final model scorecard used in the PPT narrative", fontsize=18, fontweight="bold", x=0.02, ha="left")
    for ax, (key, title, subtitle) in zip(axes.ravel(), metrics):
        vals = [r[key] for r in FINAL_SCORECARD]
        colors = [PALETTE.get(m, "#69756f") for m in models]
        ax.bar(range(len(models)), vals, color=colors, width=0.72)
        if key == "mean_speed":
            ax.axhline(1.0, color="#8a9690", linestyle="--", linewidth=1)
        style_ax(ax, f"{title} ({subtitle})", key)
        ax.set_xticks(range(len(models)))
        ax.set_xticklabels(models, rotation=35, ha="right")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    savefig("final_scorecard_bars.png")


def plot_tradeoff_scatter() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    scatter_specs = [
        ("mean_speed", "jerk", "Speed vs jerk", "mean speed", "action jerk"),
        ("mean_speed", "cot", "Speed vs energy", "mean speed", "CoT"),
        ("anti_phase", "jerk", "Gait proxy vs smoothness", "anti_phase", "action jerk"),
    ]
    for ax, (xkey, ykey, title, xlabel, ylabel) in zip(axes, scatter_specs):
        for row in FINAL_SCORECARD:
            x = row[xkey]
            y = row[ykey]
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            model = row["model"]
            ax.scatter(x, y, s=80, color=PALETTE.get(model, "#555"), edgecolor="white", linewidth=1.2, zorder=3)
            ax.annotate(model, (x, y), xytext=(6, 5), textcoords="offset points", fontsize=8)
        if xkey == "mean_speed":
            ax.axvline(1.0, color="#8a9690", linestyle="--", linewidth=1)
        style_ax(ax, title, ylabel)
        ax.set_xlabel(xlabel)
    fig.suptitle("Scorecard trade-offs: why one metric is not enough", fontsize=17, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    savefig("tradeoff_scatter.png")


def plot_alpha_beta_context(grouped: dict[str, dict[str, list[tuple[int, float]]]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    for model in ["Alpha"]:
        for tag in ["Eval/reward", "eval/episode_return"]:
            series = grouped.get(model, {}).get(tag, [])
            if series:
                ax.plot([x / 1000 for x, _ in series], [y for _, y in series],
                        label=f"{model} {tag}", color=PALETTE[model], linewidth=2)
    style_ax(ax, "Alpha had reward curves but no gait scorecard", "reward")
    ax.set_xlabel("training steps (k)")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    for tag, color in [("gait/x_velocity", "#315d6a"), ("contacts/diagonal_sync", "#2f8f4e")]:
        series = grouped.get("Beta", {}).get(tag, [])
        if not series:
            continue
        ax.plot([x / 1000 for x, _ in series], [y for _, y in series],
                label=tag, color=color, linewidth=1.4, alpha=0.85)
    style_ax(ax, "Beta started gait logging, later exposed seed risk", "logged value")
    ax.set_xlabel("training steps (k)")
    ax.legend(frameon=False, fontsize=8)
    fig.suptitle("PPT Page 1 context: reward success did not yet mean stable gait", fontsize=17, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    savefig("alpha_beta_context.png")


def write_markdown(grouped: dict[str, dict[str, list[tuple[int, float]]]]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tag_counts = {model: len(tags) for model, tags in grouped.items()}
    md = f"""# RLAP TD3 TensorBoard Model Analysis

這份分析照 PPT 的三頁架構整理，輸出為 Markdown + PNG 圖表，不做 web。

資料來源：

- TensorBoard event files：`RL_Labcowork/output/**/tb/**/events.out.tfevents.*`
- Gamma / BetaPrime / Theta 的最終 scorecard 數值：專案報告與 changelog 中已整理的 deterministic evaluation 結果
- Alpha 沒有九大步態 scorecard，因此只用 reward / loss 類 TensorBoard 訊號說明早期限制

## 圖表檔案

| File | 用途 |
|---|---|
| `figures/alpha_beta_context.png` | PPT 第 1 頁：Alpha/Beta 的早期困境 |
| `figures/tb_evaluation_curves.png` | PPT 第 2 頁：Gamma/BetaPrime/Theta 的 TensorBoard eval 曲線 |
| `figures/final_scorecard_bars.png` | PPT 第 3 頁：最終模型 scorecard 比較 |
| `figures/tradeoff_scatter.png` | 指標 trade-off：速度、jerk、CoT、anti_phase 的互相拉扯 |
| `data/tb_selected_scalars.csv` | 圖表用 TensorBoard scalar 精簡資料 |
| `data/final_scorecard.csv` | 最終 scorecard 表格 |

## PPT Page 1 - 困境一：Reward 高，不代表步態可信

Alpha 是自寫 TD3，TensorBoard 裡主要是 `Eval/reward`、`Train/reward`、loss 等一般 RL 指標。
這能確認模型有在學，但不能回答「是不是自然、穩定、省力地走」。

Beta 改用 SB3 TD3 與 `RealisticGaitWrapper` 後，開始記錄 `gait/x_velocity`、`contacts/diagonal_sync`
等步態訊號，主觀影片也最自然。但後來 multi-seed 才發現 Beta seed 1/2 會 fast-fall。

重點結論：

- Alpha：能看 reward，但沒有同規格 gait scorecard。
- Beta：自然步態基準成立，但 seed 穩定性不足。
- 困境不是 TD3 完全學不會，而是 reward 會讓模型學到站著、暴衝或摔倒止損等錯誤 attractor。

![Alpha/Beta context](figures/alpha_beta_context.png)

## PPT Page 2 - 困境二：量化後發現指標彼此 trade-off

Gamma 不是重寫 wrapper，而是在同一個 `RealisticGaitWrapper` 裡做 reward 參數搜尋。
TensorBoard eval 曲線顯示，`episode_length` 可以很快穩到 1000，但速度、jerk、CoT、
diagonal_sync 不會同時最佳。

分支解讀：

| 分支 | 技術做法 | 觀察 |
|---|---|---|
| Gamma 04-08 | `forward_gated`、`antiphase_gated`、`tent`、`smooth_weight`、`gait_weight`、`intra_weight` | 可以逐步修站著、超速、抖動，但每次修一項都會牽動另一項 |
| BetaPrime | 從 Beta checkpoint 加 `gait_speed_gate=0.3` 微調 | 25k checkpoint 指標最好，但依賴成功的 Beta 起點 |
| Theta / 15A | `ctrl_schedule` 修 fast-fall，再用 `forward_weight` resume 補速度 | 走滿 1000、速度接近目標、jerk 仍低，是目前穩定化分支的 final |

核心 trade-off：

- 速度準不代表最平滑。
- `anti_phase` / `regularity` 漂亮不代表 CoT 和觀感最好。
- `ctrl_weight` 太重會讓步態自然、省力，但也可能慢。
- `forward_weight` 增加可以補速度，但需要監控 jerk / CoT 是否惡化。

![TensorBoard evaluation curves](figures/tb_evaluation_curves.png)

![Trade-off scatter](figures/tradeoff_scatter.png)

## PPT Page 3 - 解決與最終結果

最終結果不只看 reward，而是用 scorecard 共同檢查：

```text
ep_len, mean_speed, speed_error,
contact_regularity, anti_phase, diagonal_sync,
action_jerk, CoT, uprightness
```

| Model | Role | ep_len | speed | speed_error | jerk | CoT | diagonal_sync | upright |
|---|---|---:|---:|---:|---:|---:|---:|---:|
"""
    for row in FINAL_SCORECARD:
        if row["model"] in ("Gamma-04", "Gamma-05", "Gamma-06", "Gamma-07", "Gamma-08"):
            continue
        md += (f"| {row['model']} | {row['role']} | {row['ep_len']:.0f} | "
               f"{row['mean_speed']:.3f} | {row['speed_error']:.3f} | {row['jerk']:.3f} | "
               f"{row['cot']:.3f} | {row['diagonal_sync']:.3f} | {row['uprightness']:.3f} |\n")

    md += f"""
![Final scorecard](figures/final_scorecard_bars.png)

## Model-by-model interpretation

### Alpha

自寫 PyTorch TD3 的起點。它解決了基本訓練流程與 Ant-v5 reward shaping，但當時只能看 reward、
loss 和影片，還不能用九大指標公平比較步態。

### Beta

第一個自然步態基準。`ctrl_weight=5.0` 讓動作小、平滑、省力，seed 0 的 `jerk=0.028`、
`CoT=1.02` 很漂亮。但 multi-seed 後發現成功率只有 1/3，所以它是視覺目標，不是穩定方法。

### Gamma 04-08

這條線把問題改成「先穩定會走，再調步態品質」。Gamma 04 修掉站著/原地踏步；
Gamma 06 用 tent speed gate 修超速；Gamma 07 速度最準；Gamma 08 代理步態指標最好。
但整體暴露出 reward trade-off：指標單項冠軍不一定是最好模型。

### BetaPrime

從成功的 Beta checkpoint 出發，加入 gait gate 拆掉站著 gait 分。`BetaPrime-25k` 是最佳單一
checkpoint：speed 0.983、jerk 0.037、CoT 0.960。不過它依賴 Beta 成功起點。

### Theta / 15A

Theta 回頭修 Beta 從零訓練不穩的根因。先用 `ctrl_schedule` 避免 early fast-fall，再用
`forward_weight` resume 補速度。15A 最終達到 ep_len 1000、speed 0.913、jerk 0.052、
diagonal_sync 0.744，是目前最適合放在 Project Result 的 final branch。

## Available TensorBoard scalar groups

這次抽到的 scalar tag group 數：

"""
    for model, count in sorted(tag_counts.items()):
        md += f"- {model}: {count} tags\n"

    md += """
## Notes

- `Gamma-05` 沒有本機 TensorBoard event file，因此訓練曲線圖不包含 Gamma-05；最終 scorecard 仍來自已整理報告。
- `BetaPrime-25k` 是 checkpoint 結果，TensorBoard curve 也包含同一次 fine-tuning 後續點。
- `Theta-15A` 目前是 seed 1 的最佳結果，仍建議補 seed 2 驗證。
"""
    (OUTPUT / "model_analysis_from_tb.md").write_text(md, encoding="utf-8")


def main() -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    rows = extract_all()
    write_csv(rows)
    grouped = by_model_tag(rows)
    plot_alpha_beta_context(grouped)
    plot_training_curves(grouped)
    plot_final_scorecard()
    plot_tradeoff_scatter()
    write_markdown(grouped)

    print(f"Wrote {len(rows)} scalar rows")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
