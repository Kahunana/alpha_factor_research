"""Report Generator

Generate a human-readable markdown report from the backtest metric output files.
"""
import os
from datetime import datetime
import pandas as pd
from config import RESULT_OUTPUT_DIR, REPORT_DIR
from utils import ensure_directory


class ReportGenerator:
    def __init__(self):
        self.result_dir = RESULT_OUTPUT_DIR
        self.report_dir = REPORT_DIR
        ensure_directory(self.report_dir)

    def _collect_metrics(self):
        metrics_files = [
            f for f in os.listdir(self.result_dir)
            if f.endswith("_metrics.csv")
        ]
        metrics = []
        for file_name in sorted(metrics_files):
            path = os.path.join(self.result_dir, file_name)
            df = pd.read_csv(path)
            metrics_dict = {row["metric"]: row["value"] for _, row in df.iterrows()}
            metrics.append({
                "scenario": file_name.replace("_metrics.csv", ""),
                **metrics_dict,
            })
        return metrics

    def generate_report(self):
        metrics = self._collect_metrics()
        if not metrics:
            raise ValueError("No metric files found in result directory to generate report.")

        report_path = os.path.join(self.report_dir, "strategy_report.md")
        content = self._render_markdown(metrics)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Generated report: {report_path}")
        return report_path

    def _render_markdown(self, metrics):
        header = [
            "# Strategy Backtest Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary of Backtest Metrics",
            "",
        ]

        table_header = (
            "| Scenario | CAGR | Annual Vol | Sharpe | Sortino | Calmar | Win Rate | Max Drawdown | MDD Duration |"
        )
        table_divider = "|---|---|---|---|---|---|---|---|---|"
        rows = [table_header, table_divider]
        for item in metrics:
            rows.append(
                "| {} | {:.2%} | {:.2%} | {:.3f} | {:.3f} | {:.3f} | {:.2%} | {:.2%} | {} |".format(
                    item.get("scenario", "unknown"),
                    float(item.get("cagr", 0.0)),
                    float(item.get("annual_volatility", 0.0)),
                    float(item.get("sharpe", 0.0)),
                    float(item.get("sortino", 0.0)),
                    float(item.get("calmar", 0.0)),
                    float(item.get("win_rate", 0.0)),
                    float(item.get("max_drawdown", 0.0)),
                    int(item.get("max_drawdown_duration", 0)),
                )
            )

        image_files = [
            f for f in os.listdir(self.report_dir) if f.endswith(".png")
        ]
        image_section = ["", "## Visualizations", ""]
        if image_files:
            for image in sorted(image_files):
                image_section.append(f"![{image}]({image})")
        else:
            image_section.append("No visualization files were generated.")

        analysis_files = [
            f for f in os.listdir(self.report_dir) if f.endswith("_analysis.md")
        ]
        analysis_section = ["", "## Analysis Notes", ""]
        if analysis_files:
            for file_name in sorted(analysis_files):
                path = os.path.join(self.report_dir, file_name)
                with open(path, "r", encoding="utf-8") as f:
                    analysis_section.append(f.read())
                    analysis_section.append("")
        else:
            analysis_section.append("No additional analysis summaries were found.")

        notes = [
            "", "## Notes", "",
            "- This report summarizes the backtest metric files generated under `result/`.",
            "- Detailed analysis files and charts are saved under the `report/` folder.",
        ]
        return "\n".join(header + rows + image_section + analysis_section + notes)


if __name__ == "__main__":
    ReportGenerator().generate_report()
