# Runnable Module (Step1)

当前包含两个模块：

- `step1_fetch_history.py`（拉取数据）
- `step2_build_fv.py`（清洗不合格数据并直接产出FV矩阵）

功能：

- 拉取 BTC 15m 历史市场列表与 snapshots
- 清洗不合格 snapshots（缺列、样本不足、缺失率过高）
- 直接构建 `fair_values_matrix_from_snapshots.csv`

## 配置

在 `config.py` 里明文填写：

```python
API_KEY = "YOUR_POLYBACKTEST_API_KEY"
```

也可用环境变量临时覆盖（优先级更高）：

```bash
set POLYBACKTEST_API_KEY=your_key
```

## Quick Start

```bash
python step1_fetch_history.py --limit 50 --out history_markets_50.csv
python step1_fetch_history.py --market-id <ID> --snapshots-out history_snapshots.csv
python step1_fetch_history.py --batch-csv history_markets_50.csv --snapshots-dir snapshots_50
python step2_build_fv.py --snapshots-dir snapshots_50 --matrix-out fair_values_matrix_from_snapshots.csv
python step2_build_fv.py --snapshots-dir snapshots_50 --legacy-data-dir ..\..\..\data --matrix-out fair_values_matrix_full.csv
```

## Dependencies

```bash
pip install -r requirements.txt
```

## 原理说明

详细原理见：`MATRIX_GENERATION.md`
