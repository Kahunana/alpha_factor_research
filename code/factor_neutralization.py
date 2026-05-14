# Factor Neutralization Module
# Implement industry neutralization and market capitalization neutralization
import numpy as np
import pandas as pd

class FactorNeutralizer:
    def _normalize_stock_and_date(self, df):
        if df is None or df.empty:
            return df
        df = df.copy()
        if "stock" in df.columns:
            df["stock"] = df["stock"].astype(str)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def neutralize_by_industry(self, factor_data, industry_label_df):
        if factor_data is None or factor_data.empty:
            return factor_data

        industry_label_df = self._normalize_stock_and_date(industry_label_df)
        if industry_label_df is None or industry_label_df.empty:
            return factor_data

        if "industry" not in industry_label_df.columns:
            return factor_data

        factor_df = factor_data.copy()
        if "date" in industry_label_df.columns:
            merged = factor_df.merge(
                industry_label_df[["date", "stock", "industry"]],
                on=["date", "stock"],
                how="left",
            )
        else:
            merged = factor_df.merge(
                industry_label_df[["stock", "industry"]],
                on="stock",
                how="left",
            )

        factor_cols = [c for c in factor_df.columns if c not in ["date", "stock"]]
        merged[factor_cols] = merged.groupby(["date", "industry"])[factor_cols].transform(
            lambda x: x - x.mean()
        )
        return merged[["date", "stock"] + factor_cols]

    def neutralize_by_market_cap(self, factor_data, cap_data):
        if factor_data is None or factor_data.empty:
            return factor_data

        cap_data = self._normalize_stock_and_date(cap_data)
        if cap_data is None or cap_data.empty:
            return factor_data

        cap_columns = [c for c in cap_data.columns if c.lower() in ["market_cap", "marketcap", "mktcap", "size"]]
        if not cap_columns:
            return factor_data

        cap_key = cap_columns[0]
        factor_df = factor_data.copy()
        if "date" in cap_data.columns:
            merged = factor_df.merge(
                cap_data[["date", "stock", cap_key]],
                on=["date", "stock"],
                how="left",
            )
        else:
            merged = factor_df.merge(
                cap_data[["stock", cap_key]],
                on="stock",
                how="left",
            )

        merged[cap_key] = pd.to_numeric(merged[cap_key], errors="coerce").replace(0, np.nan)
        factor_cols = [c for c in factor_df.columns if c not in ["date", "stock"]]

        for date, group in merged.groupby("date"):
            valid = group[cap_key].notna()
            if valid.sum() < 3:
                continue
            cap_vector = np.log(group.loc[valid, cap_key].astype(float).values)
            design = np.vstack([np.ones_like(cap_vector), cap_vector]).T
            for col in factor_cols:
                values = group.loc[valid, col].astype(float).values
                beta, _, _, _ = np.linalg.lstsq(design, values, rcond=None)
                residuals = values - design.dot(beta)
                merged.loc[group.index[valid], col] = residuals

        return merged[["date", "stock"] + factor_cols]

    def dual_neutralization(self, factor_df, industry_df, cap_df):
        """Execute industry-first then market-cap dual neutralization"""
        temp_result = self.neutralize_by_industry(factor_df, industry_df)
        final_result = self.neutralize_by_market_cap(temp_result, cap_df)
        return final_result