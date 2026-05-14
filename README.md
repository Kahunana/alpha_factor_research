# Alpha Factor Research

这是一个基于 alpha-factor 的量化策略研究项目。项目的核心代码位于 `code/` 目录，支持因子计算、行业和市值中性化、组合构建、回测以及报告生成。

## 目录结构

- `code/`
  - `run_all.py`：主入口脚本，执行固定划分回测、滚动回测并生成报告。
  - `backtest_engine.py`：回测流程与绩效计算。
  - `factor_calculator.py`：因子计算逻辑。
  - `factor_neutralization.py`：行业和市值中性化。
  - `portfolio_engine.py`：组合构建与多空回测逻辑。
  - `report_generator.py`：生成策略报告。
  - `utils.py`：公共工具函数。
- `data/raw_data/`：原始价格数据和可选行业、市值数据。
- `data/processed_factor/`：因子计算结果输出目录。
- `result/`：回测结果输出目录。
- `report/`：回测报告输出目录。

## 依赖

请使用 Python 3.8+ 执行。建议在虚拟环境中安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

依赖中已经包含 `pandas`、`numpy` 和 `matplotlib`。

## 因子说明与模型

项目构建了多维 alpha 因子组合，包括：

- `mom_1m`：1 个月动量
- `mom_6m`：6 个月动量
- `short_rev`：短期反转
- `vol_1m`：月度波动率
- `vol_of_vol`：波动率的波动
- `high_52w`：距离 52 周新高的程度
- `intraday_trend`：月收盘价与月开盘价趋势
- `amihud_illiq`：阿米哈德缺陷度指标
- `volume_trend`：成交量趋势
- `pv_corr`：价格与成交量相关性
- `skew_3m`：收益偏度

所有因子先标准化后求平均，构建复合得分；组合采用长/短分位组构建多空组合。

## 运行步骤

1. 确认原始数据文件已放入 `data/raw_data/`。
   - 支持的价格数据文件为 CSV 格式。
   - 最低要求列：`close`。
   - 可选列：`date` / `timestamp` / `datetime`、`stock` / `symbol`、`open`、`high`、`low`、`volume`。
2. 从项目根目录运行：

```bash
python3 code/run_all.py
```

也可以运行根目录入口：

```bash
python3 run_all.py
```

回测完成后，结果文件将保存到 `result/`，报告文件保存到 `report/`。

## 输出说明

- `result/fixed_split_backtest_nav.csv`：固定划分回测资产净值。
- `result/fixed_split_backtest_returns.csv`：固定划分回测每周期收益率。
- `result/fixed_split_backtest_metrics.csv`：固定划分回测绩效指标。
- `result/rolling_walk_backtest_nav.csv`：滚动回测资产净值。
- `result/rolling_walk_backtest_returns.csv`：滚动回测每周期收益率。
- `result/rolling_walk_backtest_metrics.csv`：滚动回测绩效指标。

- `report/strategy_report.md`：回测指标汇总报告，包含 CAGR、Sharpe、最大回撤等核心结果。
- `report/*_analysis.md`：单个回测场景的风险暴露、因子相关性与分位组分析摘要。
- `report/*_nav.png`：资产净值曲线图。
- `report/*_drawdown.png`：回撤曲线图。
- `report/*_factor_correlations.png`：因子与收益相关性图表。

## 数据说明

- 如果 `data/raw_data/` 中没有行业或市值文件，策略仍然可以运行；中性化模块会在数据缺失时跳过对应处理。
- 若要补充行业分类，请添加包含列 `date`、`stock` 和 `industry` 的 CSV 文件。
- 若要补充市值数据，请添加包含列 `date`、`stock` 和 `market_cap`（或 `marketcap` / `size`）的 CSV 文件。

## 说明

目前项目默认使用 `data/raw_data/` 下的首个 CSV 原始价格文件进行因子计算。推荐将币种或股票价格数据整理为标准时间序列格式，以获得更稳定的因子与回测结果。
