# Beta Prime Model

Beta Prime 是從 Beta checkpoint 出發的 curriculum fine-tuning 分支。它對應原始實驗中的 12。

## Files

| File | Purpose |
|---|---|
| `finetune_beta_prime.py` | 載入 Beta 模型，加入 gait speed gate 做微調 |

## Technical Method

Beta Prime 不從零訓練，而是：

1. 載入已會走的 Beta checkpoint
2. 換上 gait gate reward
3. 清空 replay buffer，避免混用舊 reward 的資料
4. `learning_starts=0`，第一個 episode 就用載入的策略開始收集
5. 用較小 learning rate 與 action noise 微調

主要設定：

```text
gait_mode = legacy
forward_mode = deviation
reward_structure = additive
gait_speed_gate = 0.3
learning_rate = 1e-4
action_noise = 0.03
```

Gait gate 公式：

```text
p = clip(max(x_velocity, 0) / 0.3, 0, 1)
r_gait = r_gait * p^2 * (3 - 2p)
```

這樣可以讓低速站著時拿不到 gait 分，但已會走的模型在正常速度下仍保留原本步態。

## Best Result

Beta Prime 的最佳點不是 final model，而是約 25k 的 checkpoint：

| Metric | Beta Prime 25k |
|---|---:|
| ep_len | 1000 |
| mean_speed | 0.983 |
| speed_error | 0.108 |
| jerk | 0.037 |
| CoT | 0.960 |
| diagonal_sync | 0.678 |
| anti_phase | 0.245 |
| uprightness | 0.990 |

## Limitation

Beta Prime 很強，但依賴 Beta checkpoint。後來 multi-seed 發現 Beta 只有 seed 0 成功，seed 1/2 會 fast-fall，因此 Beta Prime 是最佳單一 checkpoint，但不是完整解決 multi-seed 穩定性的最終方法。
