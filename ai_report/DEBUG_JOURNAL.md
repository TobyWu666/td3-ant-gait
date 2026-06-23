# Debug 日誌整理

這份文件把專案中主要 debug 事件整理成老師可讀的形式。完整原始紀錄可看 `03_debug_logs/CHANGELOG_experiment_log.md` 與各 spec 檔。

## Debug 1：Alpha 站著不動 attractor

### 現象

Ant-v5 訓練時，模型容易收斂到站著不動，或只做很小的動作。

### AI 協助診斷

AI 協助分析 reward 結構，發現 Ant-v5 預設 `healthy_reward=1.0` 讓站著不動也能每步拿穩定分數：

```text
standing reward ≈ healthy_reward - ctrl_cost - contact_cost
               ≈ +1.0
```

走路雖然有 forward reward，但需要承擔摔倒風險，因此 TD3 可能選擇低風險的站著策略。

### 解法

- 降低 `healthy_reward`
- 提高 `contact_cost_weight`
- 保留 `forward_reward_weight=1.0`
- 加入邊界懲罰與出界 terminal
- 加入 action magnitude / action difference penalty

### 證據

- `04_specs_and_design/alpha_standing_attractor_debug.md`
- `03_debug_logs/alpha_training_run.log`

---

## Debug 2：Alpha 無法公平量化步態

### 現象

Alpha 有 reward、loss、checkpoint，但無法直接回答「步態是否自然」。

### 根因

Alpha 是自寫 TD3 `.pt` 模型，當時還沒有 gait metrics，也不能直接套後來 SB3 的 scorecard pipeline。

### 解法

後續 Beta / Gamma 建立：

- `RealisticGaitWrapper`
- TensorBoard gait logging
- `gait_metrics.py`
- `eval_scorecard.py`

### 證據

- `05_tb_analysis/model_analysis_from_tb.md`
- `04_specs_and_design/gamma_claude_task_spec.md`

---

## Debug 3：Beta 看起來自然，但 hidden reward loophole

### 現象

Beta seed 0 看起來最自然，jerk 與 CoT 很漂亮，但後來發現設計上仍有隱性站著 attractor。

### AI 協助診斷

03 / Beta 的 `legacy` gait reward 是逐幀看對角同步。四腳站著時，同對角腳也同步，因此 `r_gait` 可能偏高。

另外：

```text
forward_mode = deviation
r_forward = -|x_velocity - target_speed|
```

站著時會被扣分，但配合 `alive`、`gait`、`ctrl` 後仍可能形成複雜 attractor。

### 解法

04 / Gamma 改成：

- `forward_mode="progress"`
- `reward_structure="forward_gated"`
- `gait_mode="antiphase_gated"`

### 證據

- `04_specs_and_design/gamma_claude_task_spec.md`
- `03_debug_logs/CHANGELOG_experiment_log.md`

---

## Debug 4：Gamma 修單一問題會製造新的 trade-off

### 現象

04-08 逐步修掉站著、超速、抖動，但每次修一項都影響另一項。

### 典型例子

| Version | 修到的問題 | 新問題 |
|---|---|---|
| Gamma 04 | 站著/原地踏步 | 動作粗、CoT 高 |
| Gamma 05 | 步態 proxy 變好 | 超速 |
| Gamma 06 | 超速與 jerk | 踏步變柔 |
| Gamma 07 | 速度最準 | jerk / CoT 回升 |
| Gamma 08 | regularity / anti_phase 最好 | 觀感與能耗不一定最好 |

### 解法

不再只追單一指標，而是用 scorecard 作為護欄，搭配影片主觀判斷。

### 證據

- `05_tb_analysis/figures/tb_evaluation_curves.png`
- `05_tb_analysis/figures/final_scorecard_bars.png`
- `05_tb_analysis/model_analysis_from_tb.md`

---

## Debug 5：11 從零訓練 gate 會 fast-fall

### 現象

把 Beta 直接加 `gait_speed_gate=0.3` 從零訓練，模型在 300k 探針時約 13 steps 就摔。

### AI 協助診斷

Beta 中「低速仍有 gait 分」雖然是漏洞，但早期像學習鷹架，幫模型先站穩。從零訓練直接拿掉，配合重 `ctrl=5` 與 `deviation` 速度懲罰，會讓 cold-start 進入快速摔倒。

### 解法

12 / BetaPrime 不從零訓練，而是：

- 載入已會走的 Beta checkpoint
- 清空 replay buffer
- `learning_starts=0`
- 小 learning rate / 小 action noise
- 加 gait gate 微調

### 結果

12@25k 成為最佳單一 checkpoint。

### 證據

- `03_debug_logs/CHANGELOG_experiment_log.md`
- `04_specs_and_design/beta_prime_followup_ai_spec.md`

---

## Debug 6：12 final 不如 12@25k

### 現象

12@25k 表現最佳，但 120k final 速度漂慢。

### AI 協助診斷

這代表 checkpoint selection 很重要，不能只拿 final model。訓練後期 actor 持續優化 wrapper reward，但可能偏離 scorecard 目標。

### 解法

- 固定 25k checkpoint 作為 BetaPrime 的主要結果
- 後續 12a 嘗試補 anti_phase，但未能勝過 12@25k

### 證據

- `04_specs_and_design/beta_prime_followup_ai_spec.md`
- `05_tb_analysis/data/final_scorecard.csv`

---

## Debug 7：Multi-seed 暴露 Beta 成功率只有 1/3

### 現象

Beta seed 0 成功，但 seed 1/2 fast-fall。

```text
seed 0: ep_len 1000
seed 1: about 15 steps
seed 2: about 16 steps
```

### AI 協助診斷

Beta 的成功很可能是 seed 0 的幸運起點，不是穩定配方。

### 解法

Theta / 15 回頭修從零訓練：

```text
0-100k: ctrl_weight = 0.5
100k-300k: ctrl_weight 0.5 -> 5.0
300k+: ctrl_weight = 5.0
```

讓 agent 先學會站穩與移動，再逐步加重省力約束。

### 證據

- `03_debug_logs/CHANGELOG_experiment_log.md`
- `04_specs_and_design/gamma_claude_task_spec.md`

---

## Debug 8：Theta base 穩但速度慢

### 現象

Theta / 15 修掉 fast-fall，但速度偏慢。

### AI 協助診斷

`forward_mode="deviation"` 對慢速懲罰溫和，而 `ctrl_weight=5.0` 對動作成本懲罰重，因此 agent 會選擇慢走省力。

### 解法

15A 提高 `forward_weight` 並使用 resume：

- `FORWARD_WEIGHT=1.2` 先補速度
- 後續 resume 到 `FORWARD_WEIGHT=1.8`
- 載入 model + replay buffer，不重跑整條訓練

### 結果

Theta / 15A：

```text
ep_len = 1000
mean_speed = 0.913
speed_error = 0.122
jerk = 0.052
CoT = 1.62
diagonal_sync = 0.744
uprightness = 0.991
```

### 證據

- `03_debug_logs/CHANGELOG_experiment_log.md`
- `05_tb_analysis/data/final_scorecard.csv`

---

## Debug 9：12a 失敗也是有效結果

### 現象

12a 嘗試在 legacy reward 上疊加 `anti_phase` bonus，但沒有勝過 12@25k。

### AI 協助診斷

加重 anti_phase bonus 反而可能被 legacy 主項的 diagonal sync 偏好抵消，導致 anti_phase 沒有實質提升。

### 結論

這不是單純參數沒調好，而是設計方向可能不對。因此 12@25k 仍保留為最佳 checkpoint，12a 不納入最終模型。

### 證據

- `04_specs_and_design/beta_prime_followup_ai_spec.md`
- `03_debug_logs/CHANGELOG_experiment_log.md`

---

## Debug 流程總結

本專案的 debug 方式是：

1. 用影片與 TensorBoard 發現異常。
2. 用 AI 協助拆 reward 公式與 failure mode。
3. 寫成明確 spec。
4. 跑實驗驗證。
5. 把結果寫入 changelog。
6. 若失敗，保留失敗診斷，轉成下一輪設計。
