# AI 使用總報告

## 使用 AI 的目的

本專案使用 AI 的核心目的不是代替實驗，而是加速以下工作：

- 將 TD3 / MuJoCo Ant 的實驗需求轉成可執行的訓練腳本。
- 協助分析 reward shaping 造成的錯誤 attractor。
- 把每一輪訓練結果整理成 changelog 與下一輪實驗假設。
- 將主觀影片觀察轉成可量化的 scorecard。
- 協助整理 final report、PPT 結構、老師可讀的程式包與分析圖表。

## AI 在專案中的角色分工

| AI / 工具型態 | 主要角色 | 具體產出 |
|---|---|---|
| Claude Code 規格文件 | 實驗規格與 coding guardrails | `CLAUDE.md`、`03_train_td3_spec.md`、`04_train_td3_spec.md`、`12a_train_td3_spec.md` |
| AI prompt / planning | 專題初期規劃與 TD3 背景整理 | `all prompt.md`、`rl_project_context.md` |
| Codex / coding agent | 程式整理、報告生成、TensorBoard 分析 | `RLAP_TD3_for_teacher/`、`RLAP_TD3_TB_analysis/`、本 AI 使用紀錄包 |
| CHANGELOG | 多輪實驗交接與 debug 紀錄 | 每次實驗紀錄問題、修改、結果、下一步 |

## AI 協助的具體技術工作

### 1. 從自寫 TD3 到 SB3 TD3

早期 Alpha 使用自寫 PyTorch TD3。AI 協助整理 TD3 的核心機制：

- Twin Critics
- Delayed Policy Update
- Target Policy Smoothing
- Replay Buffer
- TensorBoard logging

後來 Beta 改用 Stable-Baselines3 TD3，AI 的角色變成幫忙設計 `RealisticGaitWrapper`，把原本只追求速度的 Ant reward 改成步態導向 reward。

### 2. Reward shaping debug

AI 協助定位的主要問題：

- Ant-v5 `healthy_reward=1.0` 會讓站著不動變成穩定收入。
- 03 的 `legacy` gait reward 在四腳站著時也可能有高分。
- `forward_mode="deviation"` 讓低速變成負 reward，配上重 `ctrl_weight=5.0` 會導致 fast-fall。
- 單一 gait proxy 指標可能被 reward hacking。

對應證據：

- `04_specs_and_design/alpha_standing_attractor_debug.md`
- `04_specs_and_design/gamma_claude_task_spec.md`
- `03_debug_logs/CHANGELOG_experiment_log.md`

### 3. 建立九大步態量化指標

AI 協助將「看起來比較自然」拆成可比較的 scorecard：

```text
ep_len, mean_speed, speed_error,
contact_regularity, anti_phase, diagonal_sync,
action_jerk, CoT, uprightness
```

這讓後續可以比較 03、04-08、12、15A，而不是只看 reward 或影片。

### 4. 多輪實驗交接

每一輪失敗都沒有直接丟掉，而是被整理成下一輪設計：

| 問題 | 下一步 |
|---|---|
| Alpha 只能看 reward | 建立 gait wrapper 與 scorecard |
| Beta 自然但 seed 不穩 | 做 multi-seed 驗證 |
| Gamma 指標互相 trade-off | 不追單一 proxy，改用整體 scorecard |
| BetaPrime 指標最佳但依賴 Beta | 回頭修從零訓練穩定性 |
| Theta base 穩但慢 | 15A 用 `forward_weight` resume 補速度 |

## 人工決策與 AI 決策的分界

AI 主要提供：

- 診斷假設
- 實驗設計
- 程式草案
- 指標整理
- 報告文字
- 圖表與資料夾整理

人工主要負責：

- 判斷影片主觀觀感是否自然。
- 決定哪些模型值得繼續救。
- 決定 PPT 敘事重點。
- 核對 AI 的錯誤，例如 02 不是 SB3、04-08 不是每版重寫 wrapper。
- 決定最終採用 Theta / 15A 作為穩定化 final branch。

## 最能代表 AI 使用價值的例子

### Example 1：站著不動 attractor

AI 幫忙把「模型不走」拆成 reward 結構問題：

```text
站著不動：healthy_reward ≈ +1.0，風險低
走路：多一點 forward reward，但有摔倒風險
```

因此修正方向不是盲目加懲罰，而是移除站著收入、保持走路誘因。

### Example 2：12@25k 與 final model 的差異

AI 幫忙指出 final model 不一定最好。12 在 25k 是甜蜜點，120k 反而速度漂慢。這讓專案開始使用 checkpoint selection，而不是只看訓練最後一個模型。

### Example 3：Theta / 15A

AI 協助分析 15A 速度慢的原因：

```text
forward_mode="deviation" 對慢速懲罰溫和
ctrl_weight=5.0 對動作成本懲罰很重
agent 會選擇慢走省力
```

因此後續用 `forward_weight` resume 補速度，而不是打掉重練。

## 限制

- AI 的建議需要實驗驗證，不能直接當結論。
- AI 可能在版本關係上混淆，例如一開始曾把 02 說成 SB3，後續已修正。
- 主觀步態自然度仍需要人看影片判斷，scorecard 不能完全取代肉眼。
- 多 seed 穩定性仍需更多訓練驗證。

## 結論

AI 在本專案中的價值主要是「加速迭代與整理複雜實驗脈絡」。它幫助我們從單次 reward 訓練，進展到可診斷、可量化、可交接的實驗流程。
