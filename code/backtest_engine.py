# Backtest Engine
# Implement fixed split backtest and rolling walk-forward backtest
import os
import pandas as pd

from factor_calculator import AlphaFactorCalculator
from factor_neutralization import FactorNeutralizer
from portfolio_engine import PortfolioEngine
from utils import (
    calculate_annual_volatility,
    calculate_calmar_ratio,
    calculate_cagr,
    calculate_max_drawdown,
    calculate_max_drawdown_duration,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_win_rate,
    ensure_directory,
    validate_dataframe,
)
from config import RESULT_OUTPUT_DIR, RAW_DATA_DIR, APPLY_INDUSTRY_NEUTRAL, APPLY_MARKET_CAP_NEUTRAL

class StrategyBacktestEngine:
    def __init__(self):
        self.factor_calc = AlphaFactorCalculator()
        self.neutralizer = FactorNeutralizer()
        self.portfolio = PortfolioEngine()
        ensure_directory(RESULT_OUTPUT_DIR)

    def _load_reference_file(self, candidates):
        for name in candidates:
            path = os.path.join(RAW_DATA_DIR, name)
            if os.path.exists(path):
                df = pd.read_csv(path)
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                if "stock" in df.columns:
                    df["stock"] = df["stock"].astype(str)
                return df
        return pd.DataFrame()

    def load_raw_data(self):
        raw_price = self.factor_calc.load_price_data()
        validate_dataframe(raw_price, "原始价格数据", required_columns=["date", "stock", "close"])

        industry = self._load_reference_file([
            "industry.csv",
            "industry_classification.csv",
            "industry_labels.csv",
        ])
        if not industry.empty:
            if "industry" not in industry.columns:
                raise ValueError("行业分类数据必须包含 'industry' 列。")
            validate_dataframe(industry, "行业分类数据", required_columns=["stock", "industry"])

        market_cap = self._load_reference_file([
            "market_cap.csv",
            "marketcap.csv",
            "size.csv",
        ])
        if not market_cap.empty:
            cap_columns = [c for c in market_cap.columns if c.lower() in ["market_cap", "marketcap", "mktcap", "size"]]
            if not cap_columns:
                raise ValueError("市值数据文件必须包含 'market_cap'、'marketcap'、'mktcap' 或 'size' 列。")
            validate_dataframe(market_cap, "市值数据", required_columns=["stock", cap_columns[0]])

        return raw_price, industry, market_cap

    def compute_monthly_forward_returns(self, price_df):
        price_df = price_df.copy()
        price_df["date"] = pd.to_datetime(price_df["date"])
        price_df = price_df.sort_values(["stock", "date"])
        price_df["month"] = price_df["date"].dt.to_period("M")
        monthly = price_df.groupby(["stock", "month"])["close"].last().reset_index()
        monthly["date"] = monthly["month"].dt.to_timestamp("M")
        monthly["return_1m"] = monthly.groupby("stock")["close"].pct_change()
        monthly["forward_return"] = monthly.groupby("stock")["return_1m"].shift(-1)
        if monthly["forward_return"].dropna().empty:
            raise ValueError("无法计算前瞻收益，原始价格数据中可能缺少足够的连续月份数据。")
        return monthly[["date", "stock", "forward_return"]]

    def run_fixed_split_backtest(self):
        """Backtest under fixed training and testing period division"""
        price_df, industry_df, cap_df = self.load_raw_data()
        factor_df = self.factor_calc.generate_all_factors()
        if APPLY_INDUSTRY_NEUTRAL or APPLY_MARKET_CAP_NEUTRAL:
            factor_df = self.neutralizer.dual_neutralization(
                factor_df, industry_df, cap_df
            )
        returns_df = self.compute_monthly_forward_returns(price_df)
        merged = factor_df.merge(returns_df, on=["date", "stock"], how="inner")
        merged = merged.dropna(subset=["forward_return"])
        if merged.empty:
            raise ValueError(
                "固定划分回测中没有可用的因子与收益数据，请检查原始价格和因子数据。"
            )

        split_dates = merged["date"].sort_values().unique()
        split_point = int(len(split_dates) * 0.8)
        if split_point < 1:
            raise ValueError("固定划分回测的时间序列长度不足，无法划分训练和测试集。")
        split_threshold = split_dates[split_point]

        test_data = merged[merged["date"] >= split_threshold]
        if test_data.empty:
            raise ValueError("固定划分回测没有足够的测试区间数据，请检查数据覆盖范围。")

        nav, returns = self.portfolio.build_portfolio(test_data)
        metrics = self.evaluate_performance_metrics(nav, returns)
        self._save_results("fixed_split_backtest", nav, returns, metrics)
        print("Fixed split backtest completed.")
        return nav, returns, metrics, merged

    def run_rolling_walk_backtest(self, train_months=24, test_months=6):
        price_df, industry_df, cap_df = self.load_raw_data()
        factor_df = self.factor_calc.generate_all_factors()
        if APPLY_INDUSTRY_NEUTRAL or APPLY_MARKET_CAP_NEUTRAL:
            factor_df = self.neutralizer.dual_neutralization(
                factor_df, industry_df, cap_df
            )
        returns_df = self.compute_monthly_forward_returns(price_df)
        merged = factor_df.merge(returns_df, on=["date", "stock"], how="inner")
        merged = merged.dropna(subset=["forward_return"])
        if merged.empty:
            raise ValueError(
                "滚动回测中没有可用的因子与收益数据，请检查原始价格和因子数据。"
            )

        date_index = sorted(merged["date"].unique())
        all_returns = []

        for start in range(train_months, len(date_index), test_months):
            end = min(start + test_months, len(date_index))
            window_dates = date_index[start:end]
            if not window_dates:
                continue
            window_data = merged[merged["date"].isin(window_dates)]
            if window_data.empty:
                continue
            _, window_returns = self.portfolio.build_portfolio(window_data)
            all_returns.append(window_returns)

        if not all_returns:
            raise ValueError("滚动回测未能生成任何有效的样本窗口，请检查数据长度与时间划分。")

        combined_returns = pd.concat(all_returns).sort_index()
        combined_nav = (1 + combined_returns).cumprod().ffill().fillna(1)
        metrics = self.evaluate_performance_metrics(combined_nav, combined_returns)
        self._save_results("rolling_walk_backtest", combined_nav, combined_returns, metrics)
        print("Rolling walk-forward backtest completed.")
        return combined_nav, combined_returns, metrics, merged

    def _save_results(self, label, nav_series, return_series, metrics):
        nav_path = os.path.join(RESULT_OUTPUT_DIR, f"{label}_nav.csv")
        metrics_path = os.path.join(RESULT_OUTPUT_DIR, f"{label}_metrics.csv")
        returns_path = os.path.join(RESULT_OUTPUT_DIR, f"{label}_returns.csv")
        nav_series.rename("nav").to_csv(nav_path, header=True)
        return_series.rename("return").to_csv(returns_path, header=True)

        ordered_metrics = [
            "cagr",
            "annual_volatility",
            "sharpe",
            "sortino",
            "calmar",
            "win_rate",
            "max_drawdown",
            "max_drawdown_duration",
        ]
        metrics_rows = [
            {"metric": key, "value": metrics.get(key, 0.0)}
            for key in ordered_metrics
        ]
        pd.DataFrame(metrics_rows).to_csv(metrics_path, index=False)
        print(f"Saved {label} results: {nav_path}, {metrics_path}, {returns_path}")

    def evaluate_performance_metrics(self, nav_series, ret_series):
        """Integrated performance evaluation pipeline"""
        annual_vol = calculate_annual_volatility(ret_series)
        cagr = calculate_cagr(nav_series)
        sharpe = calculate_sharpe_ratio(ret_series)
        sortino = calculate_sortino_ratio(ret_series)
        calmar = calculate_calmar_ratio(nav_series, annual_vol)
        win_rate = calculate_win_rate(ret_series)
        mdd = calculate_max_drawdown(nav_series)
        mdd_duration = calculate_max_drawdown_duration(nav_series)
        return {
            "cagr": cagr,
            "annual_volatility": annual_vol,
            "sharpe": sharpe,
            "sortino": sortino,
            "calmar": calmar,
            "win_rate": win_rate,
            "max_drawdown": mdd,
            "max_drawdown_duration": mdd_duration,
        }

if __name__ == "__main__":
    backtest = StrategyBacktestEngine()
    backtest.run_fixed_split_backtest()
    backtest.run_rolling_walk_backtest()