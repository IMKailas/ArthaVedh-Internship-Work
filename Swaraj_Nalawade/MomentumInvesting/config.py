# config.py

# File paths and basic settings
DATA_PATH = r"C:\assignement\sem5\Internship\MomentumInvesting\NSE_NIFTY, 1D.csv"
INITIAL_BALANCE = 10000
STOP_LOSS_PERCENT = 1.0
TARGET_PROFIT_PERCENT = 2.0

# Technical indicator parameters
EMA_PERIODS = {
    'fast': 9,
    'medium': 21,
    'slow': 50
}

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

VOLUME_MA_PERIOD = 20
VOLUME_SURGE_THRESHOLD = 1.5

BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

ADX_PERIOD = 14
ADX_THRESHOLD = 25

# Price momentum settings
MOMENTUM_LOOKBACK = 10
PRICE_STRENGTH_THRESHOLD = 0  # Percentage change threshold

# Trading conditions
MIN_LOOKBACK = 50  # Start trading after indicators are established

# Logging settings
LOG_FORMAT = "%(message)s"
LOG_LEVEL = "INFO"
LOG_FILE_PREFIX = "momentum_trading_log"

# Signal generation thresholds
SIGNAL_REQUIREMENTS = {
    'trend_strength': True,     # Use ADX for trend strength
    'ema_alignment': True,      # Check EMA alignment
    'volume_confirmation': True, # Check volume surge
    'price_momentum': True,     # Check price momentum
    'rsi_filter': True,         # Use RSI filter
    'bollinger_bands': True     # Use Bollinger Bands
}
