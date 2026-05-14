from backtest_engine import StrategyBacktestEngine
from analysis_engine import AnalysisEngine
from report_generator import ReportGenerator

if __name__ == "__main__":
    engine = StrategyBacktestEngine()
    analyzer = AnalysisEngine()

    fixed_nav, fixed_returns, fixed_metrics, fixed_merged = engine.run_fixed_split_backtest()
    rolling_nav, rolling_returns, rolling_metrics, rolling_merged = engine.run_rolling_walk_backtest()

    analyzer.generate_analysis(fixed_merged, fixed_nav, fixed_returns, "fixed_split_backtest")
    analyzer.generate_analysis(rolling_merged, rolling_nav, rolling_returns, "rolling_walk_backtest")

    ReportGenerator().generate_report()
