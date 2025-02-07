# config.py

DATA_PATH = "NSE_NIFTY, 1D.csv"
INITIAL_BALANCE = 100000
RISK_PER_TRADE = 0.02  # 2% risk per trade

# Technical indicator parameters
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50
ADX_PERIOD = 14
RSI_PERIOD = 14
VOLATILITY_WINDOW = 20

# Bollinger Bands Parameters
BBANDS_PERIOD = 20
BBANDS_STDDEV = 2

# MACD Parameters
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Risk Management
STOP_LOSS_PERCENT = 1.5
PROFIT_TARGET_PERCENT = 3.0

# Logging
LOG_LEVEL = "INFO"
