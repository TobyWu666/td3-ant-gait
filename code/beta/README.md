# Beta Model

Beta 是第一個改用 Stable-Baselines3 TD3 並導入 `RealisticGaitWrapper` 的自然步態模型。

## Files

| File | Purpose |
|---|---|
| `train_beta.py` | SB3 TD3 + RealisticGaitWrapper 訓練 |
| `test_beta.py` | 載入 Beta 模型做 MuJoCo 視覺化 |

主要依賴：

| Shared file | Purpose |
|---|---|
| `../tools/gait_wrapper_03.py` | RealisticGaitWrapper reward wrapper |
| `../tools/gait_metrics.py` | 步態量化工具 |

## Technical Setting

Beta 的核心設定：

```text
gait_mode = legacy
forward_mode = deviation
reward_structure = additive
ctrl_weight = 5.0
gait_weight = 2.0
posture_weight = 2.0
alive_weight = 1.0
```

Reward 形式可概念化為：

```text
r = r_forward + r_alive + r_ctrl + r_gait + r_posture
```

其中：

```text
r_forward = - |x_velocity - target_speed|
```

## Why Beta Looked Natural

Beta 的 `ctrl_weight=5.0` 很重，使得模型不能用大幅度甩動來前進，因此容易產生小動作、平滑、省力的自然步態。

## Result

成功的 Beta seed 0：

| Metric | Value |
|---|---:|
| ep_len | 1000 |
| mean_speed | 0.940 |
| speed_error | 0.140 |
| diagonal_sync | 0.712 |
| anti_phase | 0.209 |
| jerk | 0.028 |
| CoT | 1.02 |
| uprightness | 0.986 |

## Limitation

Beta 後來在 multi-seed 驗證中暴露穩定性問題：

```text
seed 0: success
seed 1: fast-fall, about 15 steps
seed 2: fast-fall, about 16 steps
```

因此 Beta 是自然步態的視覺基準，但不是穩定可複現的最終配方。
