# Alpha Model

Alpha 是本專案的早期 TD3 版本，重點是從零手寫 TD3，並開始處理 Ant-v5 reward shaping 問題。

## Files

| File | Purpose |
|---|---|
| `train_alpha.py` | 自寫 PyTorch TD3 訓練腳本 |
| `test_alpha.py` | 載入 Alpha checkpoint 做測試與視覺化 |

Alpha 依賴的自寫 TD3 元件在：

| Shared file | Purpose |
|---|---|
| `../tools/networks.py` | Actor 與 Twin Critic network |
| `../tools/replay_buffer.py` | Replay buffer |
| `../tools/td3_agent.py` | TD3 agent update logic |

## Technical Focus

Alpha 使用自寫 TD3，包含：

- Twin Critic
- Delayed Policy Update
- Target Policy Smoothing
- Replay Buffer
- TensorBoard logging
- checkpoint saving

Reward shaping 的核心問題是 Ant-v5 原本容易出現錯誤 attractor：

- 站著不動也能靠 `healthy_reward` 有穩定收入
- 可能暴衝出界
- 動作幅度過大、抖動明顯

## Main Reward Changes

| Change | Reason |
|---|---|
| 降低 `healthy_reward` | 減少站著不動的穩定收入 |
| 提高 `contact_cost_weight` | 懲罰重踩與暴力動作 |
| `SOFT_RADIUS` / `MAX_RADIUS` | 超出活動範圍先懲罰，再截斷 episode |
| action magnitude penalty | 避免動作太大 |
| action difference penalty | 避免相鄰動作劇烈變化 |

## Limitation

Alpha 當時還沒有建立後來的九大步態 scorecard。它主要能看：

- episode reward
- eval reward
- loss
- checkpoint
- 主觀影片觀察

因此 Alpha 不適合作為最終步態品質比較基準。
