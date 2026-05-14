# Common utility functions for calculation and evaluation
import os
import numpy as np


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)


def validate_dataframe(df, name, required_columns=None):
    """Validate a DataFrame by checking required columns and basic data integrity."""
    if df is None or df.empty:
        raise ValueError(f"'{name}' 数据为空，请检查数据文件是否存在并包含有效内容。")

    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            raise ValueError(f"'{name}' 缺少必要列：{missing}。请检查数据格式。")
        missing_values = df[required_columns].isnull().any()
        if missing_values.any():
            missing_cols = missing_values[missing_values].index.tolist()
            raise ValueError(
                f"'{name}' 在 {missing_cols} 列中包含空值，请补齐数据或删除无效行。"
            )

    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_columns:
        numeric_data = df[numeric_columns].to_numpy()
        if not np.isfinite(numeric_data).all():
            raise ValueError(f"'{name}' 包含无穷或非数值数据，请检查数据清洗。")

    if required_columns and len(required_columns) > 0:
        dup_subset = [c for c in required_columns if c in df.columns]
        duplicate_rows = df.duplicated(subset=dup_subset).sum()
        if duplicate_rows > 0:
            raise ValueError(f"'{name}' 存在 {duplicate_rows} 条重复记录，请去重后重新运行。")


def calculate_cagr(nav_series):
    """Calculate Compound Annual Growth Rate"""
    if len(nav_series) < 2:
        return 0.0
    years = len(nav_series) / 12
    if years <= 0:
        return 0.0
    cagr = (nav_series.iloc[-1] / nav_series.iloc[0]) ** (1 / years) - 1
    return round(cagr, 4)


def calculate_annual_volatility(return_series):
    """Annualize monthly return volatility."""
    returns = return_series.dropna()
    if len(returns) < 2:
        return 0.0
    vol = np.std(returns, ddof=0) * np.sqrt(12)
    return round(vol, 4)


def calculate_sortino_ratio(return_series, target=0.0):
    """Calculate annualized Sortino Ratio using downside deviation."""
    returns = return_series.dropna()
    if len(returns) < 2:
        return 0.0
    downside = returns[returns < target]
    if len(downside) == 0:
        downside_std = 0.0
    else:
        downside_std = np.sqrt(np.mean((downside - target) ** 2)) * np.sqrt(12)
    if downside_std == 0 or np.isnan(downside_std):
        return 0.0
    annual_ret = returns.mean() * 12
    return round((annual_ret - target) / downside_std, 3)


def calculate_calmar_ratio(nav_series, annual_volatility=0.0):
    """Calculate Calmar Ratio as annual return divided by maximum drawdown."""
    if annual_volatility <= 0:
        return 0.0
    cagr = calculate_cagr(nav_series)
    max_dd = calculate_max_drawdown(nav_series)
    if max_dd >= 0:
        return 0.0
    return round(cagr / abs(max_dd), 3)


def calculate_win_rate(return_series):
    """Calculate the proportion of positive return periods."""
    returns = return_series.dropna()
    if len(returns) == 0:
        return 0.0
    wins = (returns > 0).sum()
    return round(wins / len(returns), 4)


def calculate_max_drawdown_duration(nav_series):
    """Calculate the maximum drawdown duration in consecutive periods."""
    if nav_series.empty:
        return 0
    peak = nav_series.iloc[0]
    max_duration = 0
    current_duration = 0
    for value in nav_series:
        if value < peak:
            current_duration += 1
        else:
            peak = value
            max_duration = max(max_duration, current_duration)
            current_duration = 0
    max_duration = max(max_duration, current_duration)
    return int(max_duration)


def calculate_max_drawdown(nav_series):
    """Calculate maximum drawdown of net asset curve"""
    rolling_max = nav_series.cummax()
    drawdown = (nav_series - rolling_max) / rolling_max
    return round(drawdown.min(), 4)

def calculate_sharpe_ratio(return_series, risk_free=0.02):
    """Calculate annualized Sharpe Ratio"""
    monthly_ret = return_series.mean()
    returns = return_series.dropna()
    if len(returns) < 2:
        return 0.0
    monthly_std = returns.std(ddof=0)
    if monthly_std == 0 or np.isnan(monthly_std):
        return 0.0
    sharpe = (monthly_ret - risk_free / 12) / monthly_std * np.sqrt(12)
    return round(sharpe, 3)