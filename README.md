# Polymarket FV Bot Research

一个面向 **Polymarket BTC 15m** 的研究型项目：  
从历史数据拉取、数据清洗、FV（公允价值）矩阵构建，到 time-split / walk-forward 统计验证。

---

## 这个仓库做什么

核心目标不是“吹收益”，而是可复现地回答：

1. 这套方法在历史上是否有统计优势？
2. 在更严格的滚动验证下是否稳定？
3. 失效时该如何继续改进？

---

## 项目亮点

- 一键拉取 PolyBacktest 历史数据（市场列表 + 快照）
- 自动清洗不合格样本并构建 FV 矩阵
- 输出可复现验证结果（JSON + Markdown）
- 附带验证图表（time-split / walk-forward）

---

## 快速开始

## 1) 安装依赖

```bash
pip install -r requirements.txt
```

## 2) 配置 API Key

编辑 `config.py`：

```python
API_KEY = "YOUR_POLYBACKTEST_API_KEY"
BASE_URL = "https://api.polybacktest.com/v2"
SLUG_PREFIX = "btc-updown-15m"
```

也支持环境变量覆盖：

```bash
set POLYBACKTEST_API_KEY=your_key
```

## 3) 拉数据

```bash
python step1_fetch_history.py --limit 50 --out history_markets_50.csv
python step1_fetch_history.py --batch-csv history_markets_50.csv --snapshots-dir snapshots_50
```

## 4) 生成 FV 矩阵

```bash
python step2_build_fv.py --snapshots-dir snapshots_50 --legacy-data-dir ..\..\..\data --matrix-out fair_values_matrix_full.csv
```

## 5) 画验证图

```bash
python plot_validation_charts.py
```

---

## 主要文件说明

- `step1_fetch_history.py`：拉市场与快照
- `step2_build_fv.py`：清洗 + 矩阵生成
- `plot_validation_charts.py`：验证图表输出
- `fair_values_matrix_full.csv`：full 数据矩阵
- `backtest_timesplit_full_validation.json`：time-split 结果
- `backtest_walkforward_full_validation.json`：walk-forward 结果
- `chart_timesplit_full.png`：time-split 图
- `chart_walkforward_full.png`：walk-forward 聚合图
- `chart_walkforward_folds_full.png`：fold 稳定性图

---

## 当前研究结论（简要）

- time-split 下仍可见正向统计信号
- full 数据 walk-forward 下显著性明显下降
- 结论：策略存在条件性 edge，但稳定性不足，需要加入成交约束与状态识别

详细结论见：

- `BACKTEST_FULL_REVALIDATION.md`
- `ARTICLE_SERIES_ALL_IN_ONE.md`

---

## 安全说明

- 仓库不包含真实 API key
- 上传前请再次检查 `config.py` 是否为占位符

---

## License

仅用于研究与学习，不构成任何投资建议。
