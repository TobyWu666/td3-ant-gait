# Evidence Index

這份索引列出本資料夾內每個證據檔代表什麼。

## 01_ai_rules

| File | 說明 |
|---|---|
| `CLAUDE.md` | repo 中的 AI agent 協作規範，定義命名、輸出、changelog、禁止重複腳本等規則 |

## 02_prompt_handoff

| File | 說明 |
|---|---|
| `initial_project_prompt_and_plan.md` | 初始 TD3 + MuJoCo Ant 專題 prompt、訓練規劃、Bug Log 與報告方向 |
| `project_context_summary.md` | 專案背景摘要 |

## 03_debug_logs

| File | 說明 |
|---|---|
| `CHANGELOG_experiment_log.md` | 最完整的實驗與 debug 時間線 |
| `alpha_training_run.log` | Alpha / 02 訓練 log，顯示 reward 與 episode progression |
| `beta_training_run.log` | Beta / 03 訓練 log，含 gait components、contact logging、training metrics |

## 04_specs_and_design

| File | 說明 |
|---|---|
| `alpha_standing_attractor_debug.md` | Ant-v5 站著不動 attractor 的 AI 診斷與解法 |
| `alpha_reward_modification_spec.md` | Alpha reward shaping 規格 |
| `beta_claude_task_spec.md` | Beta / RealisticGaitWrapper 任務規格 |
| `gamma_claude_task_spec.md` | Gamma / 步態品質優化任務規格 |
| `beta_prime_followup_ai_spec.md` | 12a 後續 AI 任務規格與失敗診斷 |

## 05_tb_analysis

| File | 說明 |
|---|---|
| `model_analysis_from_tb.md` | Codex 從 TensorBoard event logs 整理的模型分析 |
| `build_tb_analysis.py` | 純 Python TB event parser + 圖表產生腳本 |
| `figures/alpha_beta_context.png` | Alpha/Beta 困境圖 |
| `figures/tb_evaluation_curves.png` | TB eval 曲線 |
| `figures/final_scorecard_bars.png` | final scorecard 圖 |
| `figures/tradeoff_scatter.png` | 速度、jerk、CoT、anti_phase 的 trade-off 圖 |
| `data/final_scorecard.csv` | final scorecard 數據 |

## 新增整理文件

| File | 說明 |
|---|---|
| `README.md` | 本資料夾入口 |
| `AI_USAGE_REPORT.md` | AI 使用總報告 |
| `DEBUG_JOURNAL.md` | debug 日誌整理 |
| `AI_HANDOFF_RECORDS.md` | AI 接力與交接紀錄 |

## 可放進報告的一段話

> 我們使用 AI 協助完成 TD3 訓練規格、reward shaping debug、步態量化指標設計、TensorBoard 分析與實驗紀錄整理。每一輪 AI 產出的建議都透過實際訓練與 scorecard 驗證，並保留 prompt、Claude Code spec、CHANGELOG、training log 與圖表作為證據。
