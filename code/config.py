import os

# Global Configuration File
# Unified parameters and path settings for the whole project

# Backtest basic settings
TRANSACTION_COST = 0.00036
LONG_SHORT_GROUP_COUNT = 20
APPLY_INDUSTRY_NEUTRAL = True
APPLY_MARKET_CAP_NEUTRAL = True

# File path configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw_data")
FACTOR_SAVE_DIR = os.path.join(BASE_DIR, "data", "processed_factor")
RESULT_OUTPUT_DIR = os.path.join(BASE_DIR, "result")
REPORT_DIR = os.path.join(BASE_DIR, "report")

# Evaluation parameters
RISK_FREE_RATE = 0.02