# config.py

from datetime import datetime

# File and data settings
DATA_CONFIG = {
    "data_path": r"C:\assignement\sem5\Internship\optionsTrading\loadData.csv",
    "log_file": f"options_trading_log_{datetime.now().strftime('%Y%m%d')}.log"
}

# Trading parameters
TRADING_PARAMS = {
    "initial_balance": 10000,
    "risk_per_trade": 0.02,
    "stop_loss": 0.95,    # 5% stop loss
    "take_profit": 1.05   # 5% take profit
}

# Technical indicators parameters
INDICATOR_PARAMS = {
    "bollinger_window": 20,
    "bollinger_std": 2,
    "iv_window": 14,
    "iv_low_threshold": 20,
    "iv_high_threshold": 50,
    "delta_threshold": 0.7,
    "gamma_multiplier": 0.1
}

# Required data columns
REQUIRED_COLUMNS = ['open', 'high', 'low', 'close', 'time']
