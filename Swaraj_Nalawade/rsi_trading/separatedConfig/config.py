# config.py (unchanged)
from datetime import datetime

# Data Configuration
DATA_PATH = "NSE_NIFTY, 1D.csv"

# Trading Parameters
INITIAL_BALANCE = 10000
STOP_LOSS_PCT = 1.5
TARGET_PROFIT_PCT = 3.0

# Signal Parameters
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
VOLUME_SURGE_MULTIPLIER = 1.2

# Logging Configuration
LOG_FORMAT = "%(message)s"
LOG_FILENAME = f"rsi_trading_log_{datetime.now().strftime('%Y%m%d')}.log"
LOG_LEVEL = "INFO"

# Technical Indicators Configuration
MACD_SETTINGS = {
    'fast_period': 12,
    'slow_period': 26,
    'signal_period': 9
}

STOCHASTIC_SETTINGS = {
    'k_period': 14,
    'd_period': 3
}

BOLLINGER_SETTINGS = {
    'window': 20,
    'num_std': 2
}

# Trading Strategy Configuration
INITIAL_BALANCE = 10000
STOP_LOSS_PERCENT = 1.5
TARGET_PROFIT_PERCENT = 3.0
RISK_PER_TRADE = 0.02
TRANSACTION_COST_PERCENT = 0.1
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_CROSSOVER_BUY = True
MACD_CROSSOVER_SELL = True
COOLDOWN_PERIODS = 5
CSV_FILE_PATH = "NSE_NIFTY, 1D.csv"
LOG_FILE_PATH = f"rsi_trading_log_{datetime.now().strftime('%Y%m%d')}.log"
ENABLE_DEBUG_LOGGING = True
SAVE_TRADE_HISTORY = True