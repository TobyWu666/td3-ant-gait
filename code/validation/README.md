# Validation

這個資料夾放模型評估與 multi-seed 驗證腳本。

## Files

| File | Purpose |
|---|---|
| `eval_scorecard.py` | 載入 SB3 model，跑 deterministic episodes，輸出 gait scorecard |
| `multiseed_validation.py` | 重跑不同 seed，驗證 Beta/Beta Prime pipeline 是否可複現 |

## Nine Scorecard Metrics

| Metric | Meaning | Direction |
|---|---|---|
| `episode_length` | 一個 episode 撐幾步 | higher is better |
| `mean_speed` | 平均前進速度 | close to 1.0 |
| `speed_error` | 與目標速度 1.0 的平均絕對誤差 | lower is better |
| `contact_regularity` | 四腳接觸序列週期性 | higher is better |
| `anti_phase` | 兩組對角腳是否交替踩地 | higher is better |
| `diagonal_sync` | 同一組對角腳是否同步 | higher is better, but cannot be used alone |
| `action_jerk` | 相鄰動作差平方和平均 | lower is better |
| `transport_cost` | 控制力平方和除以前進距離 | lower is better |
| `uprightness` | 軀幹直立程度 | close to 1.0 |

## Important Finding

Multi-seed 驗證揭露 Beta 的 seed 穩定性不足：

```text
seed 0: success
seed 1: fast-fall
seed 2: fast-fall
```

這也是為什麼後續需要 Theta / 15A：它不是追求單一 checkpoint 的最高分，而是修從零訓練時的穩定性。
