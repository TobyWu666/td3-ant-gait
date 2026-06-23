# Theta Model

Theta 是本專案目前的最終穩定化分支。它的目標是保留 Beta 的自然步態基因，同時修掉從零訓練時的 fast-fall。

## Files

| File | Purpose |
|---|---|
| `train_theta.py` | 15 / 15A 共用訓練腳本 |

## Relationship Between Theta, 15, and 15A

原始專案裡 `train_theta.py` 對應 `15train_td3.py`。這一支腳本同時支援：

| Name | Meaning | How |
|---|---|---|
| 15 | Theta base | 從零訓練，加入 `ctrl_schedule` 修 fast-fall |
| 15A | Theta final line | 在 15 基礎上提高 `forward_weight`，並可用 checkpoint resume 補速度 |

因此：

```text
15  = 修會不會穩
15A = 穩了之後補速度
```

## Technical Setting

Theta 保留 Beta 的最終 reward 架構：

```text
gait_mode = legacy
forward_mode = deviation
reward_structure = additive
ctrl_weight = 5.0
gait_weight = 2.0
posture_weight = 2.0
alive_weight = 1.0
```

不同點是訓練初期加入 curriculum：

```text
0-100k:     ctrl_weight = 0.5
100k-300k: ctrl_weight linearly increases from 0.5 to 5.0
300k+:      ctrl_weight = 5.0
```

目的：避免早期隨機探索時 `ctrl=5.0` 太重，使模型學成快速摔倒止損。

## 15A Speed Fix

15A 發現 Theta base 已經穩、平滑、自然，但速度偏慢。因此提高 `forward_weight` 補速度：

```bash
FORWARD_WEIGHT=1.2 PYTHONPATH=. python theta/train_theta.py
```

後續 resume 可使用：

```bash
FORWARD_WEIGHT=1.8 INIT_MODEL=<model.zip> REPLAY_BUFFER=<buffer.pkl> PYTHONPATH=. python theta/train_theta.py
```

Resume 模式會：

- 載入既有 model
- 載入 replay buffer
- 移除 `ctrl_schedule`
- 固定 `ctrl_weight=5.0`
- 繼續訓練，不重跑前面流程

## Current Theta Final Result

目前可把 15A 當作 Theta final：

| Metric | Theta / 15A |
|---|---:|
| ep_len | 1000 |
| mean_speed | 0.913 |
| speed_error | 0.122 |
| jerk | 0.052 |
| CoT | 1.62 |
| diagonal_sync | 0.744 |
| uprightness | 0.991 |
| stationary_fraction | 0.002 |

## Interpretation

Theta / 15A 的重點不是單一指標最高，而是：

- 修掉 Beta seed 1 的 fast-fall
- 走滿完整 episode
- 速度接近目標
- 保留低 jerk 的自然感
- diagonal_sync 甚至高於 Beta

目前限制是仍需要更多 seeds 驗證，特別是 seed 2。
