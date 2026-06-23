# Gamma Reward Search

Gamma 代表 04-08 這條 reward 參數搜尋線。它不是每次重寫 wrapper，而是在同一個 `RealisticGaitWrapper` 參數空間裡調 reward 配方。

## Files

| File | Original stage | Purpose |
|---|---|---|
| `gamma_progress_base.py` | 04 | 先修站著不動、原地踏步與 fast-fall |
| `gamma_fusion.py` | 05 | 加強 gait、posture、smooth，拿回步態品質 |
| `gamma_tent_speed.py` | 06 | 使用 tent speed gate 修超速 |
| `gamma_speed_balanced.py` | 07 | 拉回踏步銳利度與速度準確度 |
| `gamma_proxy_best.py` | 08 | 加重 intra sync，追求 regularity / anti_phase / uprightness |

## Shared Technical Base

Gamma 系列主要使用：

```text
forward_mode = progress
reward_structure = forward_gated
gait_mode = antiphase_gated
```

核心概念：

```text
progress:
r_forward = max(0, min(x_velocity, target_speed))

forward_gated:
r_positive = forward_progress * (1 + r_gait)
```

這樣做的目的：

- 不前進就拿不到主要正 reward
- 站著與原地踏步不能靠 gait bonus 作弊
- 避免 `deviation` 在早期造成 fast-fall attractor

## Main Trade-offs Found

| Version | Improved | New issue |
|---|---|---|
| Gamma base | ep_len 穩定到 1000 | 動作較粗、速度偏快 |
| Gamma fusion | anti_phase / regularity 提升 | 速度超過目標 |
| Gamma tent speed | 修超速、降低 jerk | 踏步變柔，anti_phase 下降 |
| Gamma speed balanced | speed_error 最佳 | jerk / CoT 回升 |
| Gamma proxy best | regularity / anti_phase / uprightness 最好 | 代理指標漂亮，但能耗與觀感不一定最好 |

## Key Lesson

Gamma 證明了九大指標彼此有 trade-off：

- 速度準不代表最平滑
- anti_phase 高不代表最省力
- regularity 高不代表主觀觀感最好
- 平滑加太重會讓踏步幅度被壓掉

因此後續不再只追單一指標，而是用 scorecard 當護欄。
