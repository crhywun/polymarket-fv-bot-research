# FV 矩阵生成原理（详细版）

本文解释 `step2_build_fv.py` 如何从快照与历史数据生成 `fair_values_matrix_full.csv`。

---

## 1. 输入数据来源

矩阵训练样本由两部分合并：

- `snapshots_50/*.csv`（通过 PolyBacktest API 拉取）
- `data/btc-updown-15m-*_1s.csv`（你项目历史沉淀数据）

最终在脚本中拼接成统一训练表：

- `btc_price_diff`
- `remain_time`
- `outcome`
- `time_bucket`

---

## 2. 先清洗不合格快照

对每个 `*_snapshots.csv` 执行如下过滤（不满足即剔除）：

1. 必须包含列：`time, btc_price, price_up, price_down`
2. 原始行数 `>= min_rows`（默认 2000）
3. 关键列最大缺失率 `<= max_nan_ratio`（默认 5%）
4. 重采样到 1 秒后有效行数 `>= 600`

你当前跑出来的结果：

- 合格：32 文件
- 不合格：13 文件

---

## 3. 快照转训练特征

对合格快照：

1. `time` 转 UTC 时间并排序
2. 按 1 秒重采样（`resample("1s").last()`）
3. `btc_price/price_up/price_down` 做 `ffill + bfill`
4. 生成标签与特征：

\[
btc\_start = btc\_price_{t0}
\]

\[
btc\_diff_t = btc\_price_t - btc\_start
\]

\[
outcome =
\begin{cases}
UP, & btc\_price_{end} > btc\_start \\
DOWN, & \text{otherwise}
\end{cases}
\]

\[
remain\_time_t = (N-1) - t
\]

---

## 4. 时间分桶与价格分桶

### 4.1 时间分桶

用 `remain_time` 切 5 桶：

- `0-3m`（0~180）
- `3-6m`（181~360）
- `6-9m`（361~540）
- `9-12m`（541~720）
- `12-15m`（721+）

### 4.2 价格分桶

`btc_price_diff` 按 `diff_bin`（默认 \$20）分箱，得到 `diff_bucket`。

---

## 5. 每个桶如何计算 FV

在每个 `(time_bucket, diff_bucket)` 里：

1. 统计经验概率  
\[
up\_win\_rate = \mathbb{E}[\mathbf{1}(outcome=UP)]
\]

2. 线性拟合连续 FV（最小二乘）  
\[
FV_{up} = \beta_0 + \beta_1 \cdot btc\_price\_diff + \beta_2 \cdot remain\_time
\]

3. DOWN 侧对称处理  
\[
FV_{down} = 1 - FV_{up}
\]
对应系数写为：
- `down_intercept = 1 - up_intercept`
- `down_slope_price = -up_slope_price`
- `down_slope_time = -up_slope_time`

4. 仅保留样本量足够的桶  
`sample_size >= min_samples`（默认 500）

---

## 6. 输出矩阵字段含义

`fair_values_matrix_full.csv` 每一行是一条“可在线查表”的规则：

- `time_bucket, diff_bucket`
- `sample_size`
- `up_win_rate, down_win_rate`（经验概率）
- `up_intercept, up_slope_price, up_slope_time`（UP线性FV）
- `down_intercept, down_slope_price, down_slope_time`（DOWN线性FV）

在线策略拿到实时 `btc_diff + remain_time` 后，就能在对应桶中算出当前 `FV_up/FV_down`。

---

## 7. 你的当前结果（full数据）

命令：

```bash
python step2_build_fv.py --snapshots-dir snapshots_50 --legacy-data-dir ..\..\..\data --cleaned-out cleaned_training_table_full.csv --matrix-out fair_values_matrix_full.csv
```

产物：

- `cleaned_training_table_full.csv`
- `fair_values_matrix_full.csv`

统计：

- `snapshot_rows = 28,308`
- `legacy_rows = 1,355,220`
- `total_training_rows = 1,383,528`
- `matrix_rules = 191`

---

## 8. 为什么这个矩阵可用于交易

交易里买 YES 的直接 EV 近似为：

\[
EV_{up} \approx FV_{up} - ask_{up}
\]

当 `FV_up - ask_up > threshold` 时触发 BUY UP；DOWN 同理。  
所以矩阵本质是在给每个状态 `(time, diff)` 提供可交易的概率估计。
