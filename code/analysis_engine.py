# Analysis Engine
# Generate charts and risk exposure analysis from backtest results.
import os
import pandas as pd
import matplotlib.pyplot as plt

from config import REPORT_DIR
from utils import ensure_directory, calculate_max_drawdown


class AnalysisEngine:
    def __init__(self):
        self.report_dir = REPORT_DIR
        ensure_directory(self.report_dir)

    def generate_analysis(self, merged_df, nav_series, return_series, label):
        ensure_directory(self.report_dir)
        self._plot_nav(nav_series, label)
        self._plot_drawdown(nav_series, label)

        factor_correlations = self._calculate_factor_correlations(merged_df)
        group_summary = self._calculate_group_exposure(merged_df)

        if not factor_correlations.empty:
            self._save_factor_correlations(factor_correlations, label)
            self._plot_factor_correlations(factor_correlations, label)

        if group_summary is not None and not group_summary.empty:
            self._save_group_exposure(group_summary, label)
            self._plot_group_exposure(group_summary, label)

        self._save_analysis_summary(
            label,
            factor_correlations,
            group_summary,
            nav_series,
            return_series,
        )

    def _plot_nav(self, nav_series, label):
        path = os.path.join(self.report_dir, f"{label}_nav.png")
        plt.figure(figsize=(10, 5))
        plt.plot(nav_series.index, nav_series.values, marker="o", linestyle="-", color="#21618C")
        plt.title(f"{label} NAV Curve")
        plt.xlabel("Period")
        plt.ylabel("NAV")
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()

    def _plot_drawdown(self, nav_series, label):
        path = os.path.join(self.report_dir, f"{label}_drawdown.png")
        rolling_max = nav_series.cummax()
        drawdown = (nav_series - rolling_max) / rolling_max
        plt.figure(figsize=(10, 4))
        plt.fill_between(drawdown.index, drawdown.values, 0, color="#C0392B", alpha=0.25)
        plt.plot(drawdown.index, drawdown.values, color="#922B21")
        plt.title(f"{label} Drawdown")
        plt.xlabel("Period")
        plt.ylabel("Drawdown")
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()

    def _factor_columns(self, merged_df):
        if merged_df is None or merged_df.empty:
            return []
        excluded = {"date", "stock", "forward_return", "rank", "group", "composite_score"}
        return [
            col for col in merged_df.columns
            if col not in excluded and pd.api.types.is_numeric_dtype(merged_df[col])
        ]

    def _calculate_factor_correlations(self, merged_df):
        factor_cols = self._factor_columns(merged_df)
        if not factor_cols:
            return pd.Series(dtype=float)

        data = merged_df.dropna(subset=["forward_return"] + factor_cols)
        if data.empty:
            return pd.Series(dtype=float)

        correlations = data[factor_cols + ["forward_return"]].corr()["forward_return"].drop("forward_return")
        return correlations.abs().sort_values(ascending=False).rename("correlation")

    def _calculate_group_exposure(self, merged_df):
        if merged_df is None or merged_df.empty or "group" not in merged_df.columns:
            return None

        factor_cols = self._factor_columns(merged_df)
        if not factor_cols:
            return None

        grouped = merged_df.groupby("group")[factor_cols + ["forward_return"]].mean()
        return grouped

    def _save_factor_correlations(self, correlations, label):
        path = os.path.join(self.report_dir, f"{label}_factor_correlations.csv")
        correlations.to_csv(path, header=True)

    def _save_group_exposure(self, group_summary, label):
        path = os.path.join(self.report_dir, f"{label}_group_exposure.csv")
        group_summary.to_csv(path)

    def _plot_factor_correlations(self, correlations, label):
        path = os.path.join(self.report_dir, f"{label}_factor_correlations.png")
        plt.figure(figsize=(10, 5))
        correlations.plot(kind="bar", color="#117A65")
        plt.title(f"{label} Factor-Return Correlations")
        plt.xlabel("Factor")
        plt.ylabel("Absolute Correlation")
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()

    def _plot_group_exposure(self, group_summary, label):
        path = os.path.join(self.report_dir, f"{label}_group_exposure.png")
        plt.figure(figsize=(10, 5))
        if "forward_return" in group_summary.columns:
            group_summary["forward_return"].plot(kind="bar", color="#2874A6", alpha=0.8)
            plt.title(f"{label} Group Forward Return by Quantile")
            plt.ylabel("Average Forward Return")
            plt.xlabel("Group")
            plt.grid(axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()

    def _save_analysis_summary(self, label, factor_correlations, group_summary, nav_series, return_series):
        path = os.path.join(self.report_dir, f"{label}_analysis.md")
        content = [
            f"## {label} Analysis Summary",
            "",
            f"- Chart files generated: `{label}_nav.png`, `{label}_drawdown.png`.",
            "",
        ]

        if not factor_correlations.empty:
            content += [
                "### Factor-Ret Correlation",
                "",
                "The following factors are ranked by absolute correlation with forward returns:",
                "",
            ]
            for factor, value in factor_correlations.items():
                content.append(f"- **{factor}**: {value:.4f}")
            content += ["", ""]
        else:
            content += ["- No factor correlation analysis was generated because factor数据不足或存在缺失。", ""]

        if group_summary is not None and not group_summary.empty:
            content += [
                "### Quantile Group Exposures",
                "",
                "The average forward return for each quantile group is shown below:",
                "",
            ]
            if "forward_return" in group_summary.columns:
                for group, row in group_summary["forward_return"].items():
                    content.append(f"- Group {group}: {row:.4f}")
            content += ["", ""]
        else:
            content += ["- No quantile grouping exposure analysis could be generated.", ""]

        drawdown = calculate_max_drawdown(nav_series)
        content += [
            "### Performance Highlights",
            "",
            f"- Peak drawdown: {drawdown:.2%}",
            f"- Periods analyzed: {len(return_series.dropna())}",
            "",
            "For a deeper review, view the corresponding charts and CSV outputs in the `report/` directory.",
        ]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
