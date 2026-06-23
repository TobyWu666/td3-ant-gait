# AI 接力與交接紀錄

這份文件整理不同 AI 協作階段如何接力。重點是展示本專案不是一次性生成，而是透過多輪規格、實驗、debug、交接逐步演進。

## 接力資料來源

| Evidence | 說明 |
|---|---|
| `01_ai_rules/CLAUDE.md` | Claude Code 在 repo 中的工作規範 |
| `02_prompt_handoff/initial_project_prompt_and_plan.md` | 期末專題初始 prompt 與 TD3 規劃 |
| `04_specs_and_design/beta_claude_task_spec.md` | Beta / 03 的 Claude Code 任務規格 |
| `04_specs_and_design/gamma_claude_task_spec.md` | Gamma / 04 的 Claude Code 任務規格 |
| `04_specs_and_design/beta_prime_followup_ai_spec.md` | 12a 後續 AI 規格與失敗診斷 |
| `03_debug_logs/CHANGELOG_experiment_log.md` | 每輪實驗後留下的交接與結果紀錄 |
| `05_tb_analysis/model_analysis_from_tb.md` | Codex 從 TensorBoard 整理出的 PPT 分析 |

## 交接時間線

### Stage 0：AI 協作規範建立

`CLAUDE.md` 定義：

- 不建立重複腳本
- 共用邏輯放 `tools/`
- output 統一放 `output/`
- 每次實驗後更新 changelog
- 長時間訓練用 task agent / 背景處理

這讓 AI 不是隨意生成檔案，而是被專案規範約束。

### Stage 1：初始 TD3 專題規劃

`all prompt.md` 記錄早期規劃：

- TD3 演算法背景
- Ant-v4 / Ant-v5 環境設定
- training loop
- TensorBoard logging
- Bug Log 需求
- 報告方向

這是第一份 AI 交接文件，負責把期末專題變成可執行計畫。

### Stage 2：Beta / RealisticGaitWrapper 規格

`beta_claude_task_spec.md` 將任務從「跑 Ant」改成「讓 Ant 走得自然」：

- 使用 SB3 TD3
- 設計 `RealisticGaitWrapper`
- 記錄 reward components
- 加入 gait / contact logging
- 預先列出 attractor basin 風險

這份 spec 是 Claude Code 可直接實作的任務說明。

### Stage 3：Gamma / reward search 規格

`gamma_claude_task_spec.md` 診斷 Beta 的問題：

- legacy gait reward 可能獎勵站著
- deviation speed penalty 可能造成 fast-fall
- 需要獨立 scorecard

接著規劃：

- `forward_mode="progress"`
- `gait_mode="antiphase"`
- jerk / uprightness 指標
- eval scorecard callback

這是從單一模型走向系統化比較的交接點。

### Stage 4：CHANGELOG 作為多輪 AI handoff

`CHANGELOG_experiment_log.md` 是最重要的接力文件。它記錄每一輪：

- 做了什麼
- 為什麼做
- 結果如何
- 下一輪方向

例如：

- 04-08 reward trade-off
- 11 fast-fall
- 12 checkpoint curriculum
- 13 multi-seed 失敗
- 15 ctrl schedule
- 15A forward_weight resume

這份檔案讓後續 AI 不需要重新猜測專案歷史。

### Stage 5：Codex 整理與 TensorBoard 分析

後期 Codex 協助：

- 整理老師可看的 `RLAP_TD3_for_teacher`
- 從 TensorBoard event files 抽 scalar
- 產生 PNG 圖表
- 撰寫 PPT 三頁架構分析
- 建立本 AI 使用紀錄包

相關檔案：

- `05_tb_analysis/build_tb_analysis.py`
- `05_tb_analysis/model_analysis_from_tb.md`
- `05_tb_analysis/figures/*.png`

## AI 接力模式總結

本專案的 AI 使用方式可以概括為：

```text
Prompt / plan
  -> Claude Code task spec
  -> code implementation
  -> training result
  -> changelog debug note
  -> next AI prompt / next experiment
```

這種流程讓 AI 產出可追溯，也讓每一個失敗都能成為下一輪實驗的依據。

## 老師可看的重點

如果要在報告中簡短說明 AI 使用，可以寫：

> 本專案使用 AI 作為研究協作工具。AI 協助撰寫 TD3 訓練規格、設計 reward wrapper、分析 failure modes、整理 changelog、建立 gait scorecard 與 TensorBoard 圖表。所有 AI 建議皆透過實際訓練結果驗證，並保留在 debug 日誌與交接文件中。
