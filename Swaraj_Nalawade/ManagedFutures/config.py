# File paths and basic settings
DATA_PATH = "NSE_NIFTY, 1D.csv"
INITIAL_BALANCE = 100000
RISK_PER_TRADE = 0.02  # 2% risk per trade

# Data validation parameters
REQUIRED_COLUMNS = [
    'time', 'open', 'high', 'low', 'close', 'VWAP',
    'Upper Band #1', 'Lower Band #1', 'Volume', 'Volume MA',
    'RSI', 'RSI-based MA', 'Upper Bollinger Band', 'Lower Bollinger Band',
    'Histogram', 'MACD', 'Signal', '%K', '%D'
]

# Technical indicator parameters
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50
ADX_PERIOD = 14
VOLATILITY_WINDOW = 20

# Trend strength parameters
ADX_TREND_THRESHOLD = 25
VOLUME_CONFIRMATION_MULTIPLIER = 1.2

# RSI thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Position sizing
MAX_POSITION_SIZE = 5
POSITION_SCALING_FACTOR = 0.5  # Scale position size based on trend strength

# Entry conditions
TREND_CONFIRMATION_REQUIRED = True
VOLUME_CONFIRMATION_REQUIRED = True
MINIMUM_TREND_STRENGTH = 25

# Exit conditions
TRAILING_STOP_PERCENT = 2.0
PROFIT_TARGET_PERCENT = 3.0
STOP_LOSS_PERCENT = 1.5

# Risk management
MAX_DRAWDOWN_PERCENT = 15
MAX_TRADES_PER_DAY = 3
MIN_RISK_REWARD_RATIO = 1.5

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FILE_PREFIX = "managed_futures_log"
TRADE_HISTORY_PREFIX = "futures_trades"
DETAILED_OUTPUT = True
