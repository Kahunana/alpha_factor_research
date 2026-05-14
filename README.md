# Alpha Factor Research

This repository contains a quantitative alpha factor research project. The core implementation is in the `code/` directory and supports factor computation, optional industry and market capitalization neutralization, portfolio construction, backtesting, analysis, and report generation.

## Project Structure

- `code/`
  - `run_all.py`: main entry script that executes fixed-split backtest, rolling walk-forward backtest, analysis, and report generation.
  - `backtest_engine.py`: backtest workflow and performance evaluation.
  - `factor_calculator.py`: alpha factor computation logic.
  - `factor_neutralization.py`: industry and market-cap neutralization.
  - `portfolio_engine.py`: long-short portfolio construction and quantile grouping.
  - `analysis_engine.py`: visualization and risk/exposure analysis.
  - `report_generator.py`: markdown report creation.
  - `utils.py`: common utility functions.
- `data/raw_data/`: raw price data and optional industry/market-cap reference files.
- `data/processed_factor/`: generated factor output.
- `result/`: backtest result files.
- `report/`: report and chart output files.

## Dependencies

Use Python 3.8+ and install dependencies in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The project requires `pandas`, `numpy`, and `matplotlib`.

## Factor Definitions

The strategy builds a composite alpha score from the following monthly factors:

- `mom_1m`: 1-month momentum
- `mom_6m`: 6-month momentum
- `short_rev`: short-term reversal
- `vol_1m`: monthly volatility
- `vol_of_vol`: volatility of volatility
- `high_52w`: distance from 52-week high
- `intraday_trend`: end-of-month trend relative to opening price
- `amihud_illiq`: Amihud illiquidity measure
- `volume_trend`: 3-month volume trend
- `pv_corr`: price-volume correlation
- `skew_3m`: monthly return skewness

Each factor is standardized and averaged into a composite score. The portfolio is constructed by ranking assets by score and assigning them into quantile groups for long-short exposure.

## How to Run

1. Place raw data files into `data/raw_data/`.
   - The primary input file should be a CSV.
   - Required column: `close`.
   - Optional columns: `date` / `timestamp` / `datetime`, `stock` / `symbol`, `open`, `high`, `low`, `volume`.
2. Run from the project root:

```bash
python3 code/run_all.py
```

Alternatively, use the root wrapper:

```bash
python3 run_all.py
```

After execution, results are saved under `result/` and reports are saved under `report/`.

## Output Files

- `result/fixed_split_backtest_nav.csv`: net asset values for fixed-split backtest.
- `result/fixed_split_backtest_returns.csv`: periodic returns for fixed-split backtest.
- `result/fixed_split_backtest_metrics.csv`: performance metrics for fixed-split backtest.
- `result/rolling_walk_backtest_nav.csv`: net asset values for rolling walk-forward backtest.
- `result/rolling_walk_backtest_returns.csv`: periodic returns for rolling walk-forward backtest.
- `result/rolling_walk_backtest_metrics.csv`: performance metrics for rolling walk-forward backtest.

- `report/strategy_report.md`: consolidated backtest summary report.
- `report/*_analysis.md`: scenario-level risk exposure, factor correlation, and quantile group analysis.
- `report/*_nav.png`: net asset value charts.
- `report/*_drawdown.png`: drawdown charts.
- `report/*_factor_correlations.png`: factor correlation charts.

## Data Notes

- If there is no industry or market-cap file in `data/raw_data/`, the strategy still runs. The neutralization module skips missing reference data.
- To add industry classification, provide a CSV file containing `date`, `stock`, and `industry` columns.
- To add market-cap data, provide a CSV file containing `date`, `stock`, and one of `market_cap`, `marketcap`, or `size` columns.

## Notes

The project currently uses the first CSV file discovered in `data/raw_data/` as the raw price input. It is recommended to prepare clean, continuous time series price data for more reliable factor computation and backtesting.
