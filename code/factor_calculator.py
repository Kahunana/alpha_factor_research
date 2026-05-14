# Factor Calculation Module
# Compute momentum, reversal, volatility, liquidity and trend factors
# The model builds a composite alpha score from multiple standardized factor exposures.
import os
import numpy as np
import pandas as pd
from config import RAW_DATA_DIR, FACTOR_SAVE_DIR

class AlphaFactorCalculator:
    """Calculate monthly factor exposures for each asset.

    The pipeline constructs the following factors:
    - mom_1m: one-month momentum
    - mom_6m: six-month momentum
    - short_rev: short-term reversal
    - vol_1m: monthly return volatility
    - vol_of_vol: portfolio volatility of volatility
    - high_52w: proximity to 52-week high
    - intraday_trend: close-open trend within the month
    - amihud_illiq: liquidity-adjusted return impact
    - volume_trend: three-month volume trend
    - pv_corr: price-volume correlation
    - skew_3m: monthly skewness of returns

    A composite factor score is built later by standardizing these signals across all assets.
    """
    def __init__(self):
        self.raw_data_dir = RAW_DATA_DIR
        os.makedirs(FACTOR_SAVE_DIR, exist_ok=True)

    def _find_raw_csv(self, candidates):
        for name in candidates:
            path = os.path.join(self.raw_data_dir, name)
            if os.path.exists(path):
                return path
        return None

    def _find_any_price_file(self):
        for file_name in os.listdir(self.raw_data_dir):
            if file_name.lower().endswith(".csv"):
                return os.path.join(self.raw_data_dir, file_name)
        return None

    def _normalize_price_columns(self, df, path):
        df = df.copy()
        if "date" not in df.columns:
            if "timestamp" in df.columns:
                df = df.rename(columns={"timestamp": "date"})
            elif "datetime" in df.columns:
                df = df.rename(columns={"datetime": "date"})
        if "stock" not in df.columns:
            if "symbol" in df.columns:
                df = df.rename(columns={"symbol": "stock"})
            else:
                stock_name = os.path.splitext(os.path.basename(path))[0]
                df["stock"] = stock_name
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "close" not in df.columns:
            raise ValueError(
                "Raw price CSV must contain 'close' values."
            )
        df["stock"] = df["stock"].astype(str)
        return df

    def load_price_data(self):
        path = self._find_raw_csv([
            "prices.csv",
            "daily_price.csv",
            "price_data.csv",
            "stock_prices.csv",
        ])
        if path is None:
            path = self._find_any_price_file()
            if path is None:
                raise FileNotFoundError(
                    f"No raw price file found in {self.raw_data_dir}. "
                    "Please add a CSV file with price data."
                )

        df = pd.read_csv(path)
        df = self._normalize_price_columns(df, path)
        if "date" not in df.columns or "stock" not in df.columns or "close" not in df.columns:
            raise ValueError(
                "Raw price CSV must contain columns ['date','stock','close'] at minimum."
            )
        return df

    def _prepare_monthly_panel(self, price_df):
        price_df = price_df.copy()
        price_df["date"] = pd.to_datetime(price_df["date"])
        price_df = price_df.sort_values(["stock", "date"])
        price_df["daily_return"] = price_df.groupby("stock")["close"].pct_change()
        price_df["month"] = price_df["date"].dt.to_period("M")

        aggregation = {"close": "last", "daily_return": "std"}
        if "open" in price_df.columns:
            aggregation["open"] = "first"
        if "volume" in price_df.columns:
            aggregation["volume"] = "mean"
        if "high" in price_df.columns:
            aggregation["high"] = "max"
        if "low" in price_df.columns:
            aggregation["low"] = "min"

        monthly = price_df.groupby(["stock", "month"]).agg(aggregation).reset_index()
        monthly = monthly.rename(columns={"daily_return": "vol_1m"})

        monthly["close_1m"] = monthly.groupby("stock")["close"].shift(1)
        monthly["mom_1m"] = monthly["close"] / monthly["close_1m"] - 1
        monthly["mom_6m"] = monthly.groupby("stock")["close"].pct_change(6)
        monthly["short_rev"] = -monthly["mom_1m"]
        monthly["vol_of_vol"] = monthly.groupby("stock")["vol_1m"].rolling(6, min_periods=1).std().reset_index(level=0, drop=True)
        monthly["high_52w"] = monthly.groupby("stock")["close"].rolling(12, min_periods=1).max().reset_index(level=0, drop=True)
        monthly["high_52w"] = monthly["close"] / monthly["high_52w"] - 1

        if "open" in monthly.columns:
            monthly["intraday_trend"] = (monthly["close"] - monthly["open"]) / monthly["open"]
        else:
            monthly["intraday_trend"] = np.nan

        if "volume" in monthly.columns:
            monthly["amihud_illiq"] = monthly["mom_1m"].abs() / monthly["volume"].replace(0, np.nan)
            monthly["volume_trend"] = monthly.groupby("stock")["volume"].pct_change(3)
        else:
            monthly["amihud_illiq"] = np.nan
            monthly["volume_trend"] = np.nan

        pv_corr = []
        for (_, _), group in price_df.groupby(["stock", "month"]):
            if "volume" in group.columns and group["volume"].nunique() > 1:
                pv_corr.append(group["close"].pct_change().corr(group["volume"].pct_change()))
            else:
                pv_corr.append(np.nan)
        monthly["pv_corr"] = pv_corr

        skew = price_df.groupby(["stock", "month"])["daily_return"].skew().reset_index(name="skew_3m")
        monthly = monthly.merge(skew, on=["stock", "month"], how="left")

        monthly["date"] = monthly["month"].dt.to_timestamp("M")
        return monthly[[
            "date", "stock", "mom_1m", "mom_6m", "short_rev",
            "vol_1m", "vol_of_vol", "high_52w", "intraday_trend",
            "amihud_illiq", "volume_trend", "pv_corr", "skew_3m",
        ]]

    def generate_all_factors(self):
        """Generate monthly factor exposures and save them to the processed factor directory."""
        price_df = self.load_price_data()
        factor_df = self._prepare_monthly_panel(price_df)
        factor_df.to_csv(os.path.join(FACTOR_SAVE_DIR, "factors_monthly.csv"), index=False)
        return factor_df

if __name__ == "__main__":
    calculator = AlphaFactorCalculator()
    calculator.generate_all_factors()
