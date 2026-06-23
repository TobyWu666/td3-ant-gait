# Shared Tools

這個資料夾是所有模型分支共用的工具程式。

## Files

| File | Purpose |
|---|---|
| `networks.py` | Alpha 自寫 TD3 的 Actor / Twin Critic |
| `replay_buffer.py` | Alpha 自寫 replay buffer |
| `td3_agent.py` | Alpha 自寫 TD3 update logic |
| `gait_wrapper_03.py` | Beta/Gamma/Beta Prime/Theta 共用的 Ant reward wrapper |
| `gait_metrics.py` | 九大步態指標的計算工具 |
| `gait_train.py` | SB3 TD3 共用訓練、finetune、resume 骨架 |

## Key Idea

後期模型不再每一版複製完整訓練流程，而是：

```text
experiment file = reward config
tools/gait_train.py = shared training loop
tools/gait_wrapper_03.py = reward wrapper
tools/gait_metrics.py = scorecard metrics
```

這樣可以讓 Gamma、Beta Prime、Theta 之間保持可比較性。
