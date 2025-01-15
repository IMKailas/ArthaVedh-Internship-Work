# # config.py

from datetime import datetime

# Data Configuration
DATA_PATH = r"C:\assignement\sem5\Internship\NSE_NIFTY, 1D.csv"

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

# Initial trading parameters
INITIAL_BALANCE = 10000
STOP_LOSS_PERCENT = 1.5  # Adjusted to your script
TARGET_PROFIT_PERCENT = 3.0  # Adjusted to your script

# Risk and position management
RISK_PER_TRADE = 0.02
TRANSACTION_COST_PERCENT = 0.1

# Technical indicator thresholds
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_CROSSOVER_BUY = True  # True if MACD should be > Signal for buy
MACD_CROSSOVER_SELL = True  # True if MACD should be < Signal for sell

# Strategy parameters
COOLDOWN_PERIODS = 5  # Minimum periods between trades

# File paths
CSV_FILE_PATH = "NSE_NIFTY, 1D.csv"  # Adjusted to your script
LOG_FILE_PATH = f"rsi_trading_log_{datetime.now().strftime('%Y%m%d')}.log"  # Log file name

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Enable detailed analysis for each decision
SAVE_TRADE_HISTORY = True  # Save trades to CSV file

