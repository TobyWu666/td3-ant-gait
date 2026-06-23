# RLAP TD3 Ant Project - Teacher Review Package

這份資料夾是從原始專案複製出來的整理版，目標是讓老師可以快速看懂模型演進、必要程式碼與最終結果。

原始專案未被移動或修改；本資料夾只放報告需要的核心程式碼、共用工具、規格文件與結果摘要。

## Folder Map

| Folder | Meaning | Main content |
|---|---|---|
| `alpha/` | Alpha model | 自寫 PyTorch TD3，Ant-v5 reward shaping 起點 |
| `beta/` | Beta model | 改用 SB3 TD3 + RealisticGaitWrapper，第一個自然步態版本 |
| `gamma/` | Gamma reward-search line | 04-08 reward 參數搜尋，處理站著、超速、抖動與步態協調 trade-off |
| `beta_prime/` | Beta Prime model | 從 Beta checkpoint 做 gait gate curriculum fine-tuning |
| `theta/` | Theta final line | 用 ctrl curriculum 修 fast-fall，再用 forward_weight resume 補速度；15A 是目前 Theta final |
| `validation/` | Validation scripts | multi-seed 與 scorecard 評估 |
| `tools/` | Shared tools | TD3 agent、gait wrapper、scorecard metrics、共用訓練骨架 |
| `specs/` | Design notes | 重要 reward 設計與實驗規格 |
| `reports/` | Results | HTML report、comparison table、change log、模型演進摘要 |

## How To Read This Package

建議順序：

1. 先看 `reports/model_evolution_summary.md`
2. 再看 `theta/README.md`，了解最終模型 Theta / 15A
3. 若要看技術細節，依序看 `alpha/README.md`、`beta/README.md`、`gamma/README.md`、`beta_prime/README.md`
4. 若要驗證數值定義，看 `tools/gait_metrics.py` 與 `validation/eval_scorecard.py`

## Main Result

| Model | Role | Key result |
|---|---|---|
| Beta / original natural gait | 視覺自然基準 | 平滑、省力，但 multi-seed 不穩 |
| Beta Prime / 12@25k | 最佳單一 checkpoint | speed 0.983、jerk 0.037、CoT 0.960 |
| Theta / 15A | 最終穩定化分支 | ep_len 1000、speed 0.913、jerk 0.052、diagonal_sync 0.744 |

## Running Notes

這份整理版的程式碼保留原始 import 結構。若要從本資料夾執行，請在本資料夾根目錄執行，並加上 `PYTHONPATH=.`：

```bash
cd RLAP_TD3_for_teacher
PYTHONPATH=. python theta/train_theta.py
```

MuJoCo 離屏錄影或 Linux server 上通常需要：

```bash
MUJOCO_GL=egl
```

原始腳本內的 output 路徑仍保留實驗編號，方便追溯原始訓練紀錄。
