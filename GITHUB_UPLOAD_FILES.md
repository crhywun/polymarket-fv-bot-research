# GitHub 上传文件清单（最终）

## 上传前先改

文件：`config.py`  
把 API key 保持占位符（不要上传真实 key）：

```python
API_KEY = "YOUR_POLYBACKTEST_API_KEY"
```

---

## A. 必传（最小可复现）

### 代码

- `step1_fetch_history.py`
- `step2_build_fv.py`
- `plot_validation_charts.py`
- `config.py`
- `requirements.txt`

### 文档

- `README.md`
- `ARTICLE_SERIES_ALL_IN_ONE.md`
- `MATRIX_GENERATION.md`
- `GITHUB_UPLOAD_FILES.md`

### 关键结果

- `fair_values_matrix_full.csv`
- `backtest_timesplit_full_validation.json`
- `backtest_walkforward_full_validation.json`
- `chart_timesplit_full.png`
- `chart_walkforward_full.png`
- `chart_walkforward_folds_full.png`

---

## B. 建议上传（完整研究过程）

- `ARTICLE_SERIES_STEP1_HISTORY_FETCH.md`
- `ARTICLE_SERIES_STEP2_FV_MATRIX.md`
- `ARTICLE_SERIES_STEP3_BACKTEST_PVALUE.md`
- `ARTICLE_FULL_REVALIDATION.md`
- `ARTICLE_FULL_REVALIDATION_PLAIN.md`
- `X_THREAD_NEGATIVE_RESULT.md`
- `BACKTEST_RESULTS.md`
- `BACKTEST_VALIDATION.md`
- `BACKTEST_TIMESPLIT_VALIDATION.md`
- `BACKTEST_WALKFORWARD.md`
- `BACKTEST_FULL_REVALIDATION.md`
- `backtest_full_matrix_results.json`
- `backtest_pvalue_validation.json`
- `backtest_timesplit_pvalue_validation.json`
- `backtest_walkforward_validation.json`
- `fair_values_matrix_from_snapshots.csv`
- `rejected_files_report.csv`

---

## C. 不建议上传（体积大/中间数据）

- `snapshots_50/`
- `cleaned_training_table.csv`
- `cleaned_training_table_full.csv`
- `__pycache__/`

---

## D. 30 秒自检

1. `config.py` 没有真实 key  
2. 所有 `.md` 引用文件都存在  
3. 三张 `chart_*_full.png` 能打开  
4. README 命令可直接运行
