# Portfolio Construction Engine
# Rank stocks, group quantiles and build long-short portfolio
import numpy as np
import pandas as pd
from config import LONG_SHORT_GROUP_COUNT

class PortfolioEngine:
    def __init__(self):
        self.group_num = LONG_SHORT_GROUP_COUNT

    def rank_stocks_by_factor(self, factor_monthly_df, score_column="composite_score"):
        """Rank all stocks according to factor exposure each month"""
        df = factor_monthly_df.copy()
        factor_cols = [c for c in df.columns if c not in ["date", "stock", "forward_return"]]
        if score_column not in df.columns:
            for col in factor_cols:
                df[col] = df.groupby("date")[col].transform(
                    lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) != 0 else 0
                )
            df[score_column] = df[factor_cols].mean(axis=1)

        df["rank"] = df.groupby("date")[score_column].rank(method="first", ascending=False)
        return df

    def partition_quantile_groups(self, ranked_data):
        """Split stock pool into equal quantile groups"""
        df = ranked_data.copy()
        if df.empty:
            return df

        def assign_quantile(series):
            count = len(series)
            if count <= 1:
                return pd.Series([1] * count, index=series.index)
            rank_pct = (series.rank(method="first") - 1) / (count - 1)
            group = np.floor(rank_pct * self.group_num).astype(int) + 1
            group = group.clip(upper=self.group_num)
            return group

        df["group"] = df.groupby("date")["rank"].transform(assign_quantile)
        df["group"] = df["group"].astype("Int64")
        return df

    def construct_long_short_portfolio(self, group_return_df, forward_return_col="forward_return"):
        """Long top quantile group, short bottom quantile group"""
        df = group_return_df.copy()
        df = df.dropna(subset=[forward_return_col, "group"])
        if df.empty:
            raise ValueError("No valid monthly return data available for portfolio construction.")

        grouped = df.groupby(["date", "group"])[forward_return_col].mean().unstack(fill_value=np.nan).sort_index()
        groups = grouped.columns.tolist()
        if len(groups) == 0:
            raise ValueError("Unable to construct any quantile groups for portfolio construction.")

        if 1 in groups and self.group_num in groups:
            long_short = grouped[self.group_num] - grouped[1]
        elif len(groups) >= 2:
            top = groups[-1]
            bottom = groups[0]
            long_short = grouped[top] - grouped[bottom]
        else:
            long_short = grouped.iloc[:, 0]

        long_short = long_short.sort_index()
        nav = (1 + long_short).cumprod().ffill().fillna(1)
        return nav, long_short

    def build_portfolio(self, factor_monthly_df):
        ranked = self.rank_stocks_by_factor(factor_monthly_df)
        grouped = self.partition_quantile_groups(ranked)
        return self.construct_long_short_portfolio(grouped)
