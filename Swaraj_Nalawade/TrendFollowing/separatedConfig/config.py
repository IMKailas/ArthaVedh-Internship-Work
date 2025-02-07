
# Initial trading parameters
INITIAL_BALANCE = 10000
STOP_LOSS_PERCENT = 1.0
TARGET_PROFIT_PERCENT = 2.0

# Moving Average parameters
SHORT_MA_PERIOD = 5
LONG_MA_PERIOD = 15

# Technical indicator thresholds
RSI_BUY_THRESHOLD = 50
RSI_SELL_THRESHOLD = 50

# Stop loss settings
MAX_LOSS_PERCENT = 30  # Stop trading if balance drops below 70% of initial

# File paths
DATA_PATH = "loadData.csv"

# Required columns in input data
REQUIRED_COLUMNS = [
    'close',
    'VWAP',
    'RSI',
    'Upper Bollinger Band',
    'Lower Bollinger Band'
]

# Logging settings
LOG_FORMAT = "%(asctime)s - %(message)s"
LOG_LEVEL = "INFO"
SAVE_TRADE_HISTORY = True

# Trading rules
USE_VWAP = True  # Consider VWAP in entry decisions
USE_RSI = True   # Consider RSI in entry decisions
