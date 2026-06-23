# RLAP TD3 TensorBoard Model Analysis

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
| Beta | natural baseline | 1000 | 0.940 | 0.140 | 0.028 | 1.020 | 0.712 | 0.986 |
| BetaPrime-25k | best checkpoint | 1000 | 0.983 | 0.108 | 0.037 | 0.960 | 0.678 | 0.990 |
| Theta-15A | theta final | 1000 | 0.913 | 0.122 | 0.052 | 1.620 | 0.744 | 0.991 |

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

- Alpha: 4 tags
- Beta: 18 tags
- BetaPrime: 30 tags
- Gamma-04: 30 tags
- Gamma-06: 30 tags
- Gamma-07: 30 tags
- Gamma-08: 30 tags
- Theta-15A: 30 tags

## Notes

- `Gamma-05` 沒有本機 TensorBoard event file，因此訓練曲線圖不包含 Gamma-05；最終 scorecard 仍來自已整理報告。
- `BetaPrime-25k` 是 checkpoint 結果，TensorBoard curve 也包含同一次 fine-tuning 後續點。
- `Theta-15A` 目前是 seed 1 的最佳結果，仍建議補 seed 2 驗證。
