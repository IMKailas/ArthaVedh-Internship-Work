# config.py
from datetime import datetime

DATA_CONFIG = {
    "data_path": "loadData.csv",
    "log_file": f"options_trading_log_{datetime.now().strftime('%Y%m%d')}.log"
}

TRADING_PARAMS = {
    "initial_balance": 10000,
    "risk_per_trade": 0.02,
    "stop_loss": 0.95,    
    "take_profit": 1.05   
}

INDICATOR_PARAMS = {
    "bollinger_window": 20,
    "bollinger_std": 2,
    "iv_window": 14,
    "iv_low_threshold": 20,
    "iv_high_threshold": 50,
    "delta_threshold": 0.7,
    "gamma_multiplier": 0.1
}

REQUIRED_COLUMNS = ['open', 'high', 'low', 'close', 'time']