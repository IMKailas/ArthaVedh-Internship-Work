# Configuration for volatility arbitrage trading strategy

# Implied Volatility (VIX) generation range
VIX_MIN = 15.0  # Minimum VIX (%)
VIX_MAX = 35.0  # Maximum VIX (%)

# Rolling window for realized volatility
REALIZED_VOL_WINDOW = 14  # Days

# RSI period
RSI_PERIOD = 14

# Bollinger Bands period
BOLLINGER_PERIOD = 20

# Strategy thresholds
BUY_THRESHOLD = -10.0  # Difference between realized and implied volatility to trigger buy
SELL_THRESHOLD = 10.0   # Difference to trigger sell

# Profit target and stop loss
PROFIT_TARGET = 0.05  # 5% gain
STOP_LOSS = 0.02      # 2% loss

# Trade parameters
INITIAL_BALANCE = 100000  # Starting capital
TRADE_SIZE = 1000         # Number of units per trade

# Log file name
LOG_FILE = "trade_log.txt"


ATR_PERIOD = 14  # Time period for ATR calculation
