# RLAP AI 使用與除錯紀錄包

這份資料夾整理本專案如何使用 AI 協作完成 TD3 + MuJoCo Ant-v5 實驗。內容不是程式碼主包，而是給老師看的「AI 使用證據、debug 日誌、prompt / agent 交接紀錄」。

## 建議閱讀順序

1. `AI_USAGE_REPORT.md`  
   先看這份，說明 AI 在專案中的角色、貢獻、限制與人工決策。

2. `DEBUG_JOURNAL.md`  
   整理主要 bug / failure mode：站著不動、fast-fall、reward trade-off、multi-seed 不穩、12a 失敗等。

3. `AI_HANDOFF_RECORDS.md`  
   說明 Claude / Codex / prompt 規格 / changelog 如何接力，讓實驗不是單次黑箱生成。

4. `EVIDENCE_INDEX.md`  
   對照所有原始證據檔的位置。

## Folder Structure

| Folder | 內容 |
|---|---|
| `01_ai_rules/` | `CLAUDE.md`，AI agent 協作規範與專案約束 |
| `02_prompt_handoff/` | 初始 prompt、專案 context、交接規格 |
| `03_debug_logs/` | CHANGELOG 與訓練 log |
| `04_specs_and_design/` | Claude Code 任務規格、reward debug 設計文件 |
| `05_tb_analysis/` | Codex 從 TensorBoard event logs 整理出的分析與圖表 |

## 一句話總結

本專案不是只讓 AI 產生程式碼，而是把 AI 當作「協作研究助理」：用它來讀文件、提出 reward 診斷、寫實驗規格、整理 changelog、分析 TensorBoard、把失敗模式轉成下一輪實驗設計。
