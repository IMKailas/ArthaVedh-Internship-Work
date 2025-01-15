# Config file for theta decay trading strategy

# Logging configuration
LOG_FILE = "theta_decay_strategy.log"

# Trading parameters
INITIAL_BALANCE = 100000  # Initial capital
TRADE_SIZE = 10  # Number of units per trade
PROFIT_TARGET = 0.02  # 2% profit target
STOP_LOSS = 0.01  # 1% stop loss

# Volatility parameters
VIX_MIN = 10  # Minimum implied volatility
VIX_MAX = 30  # Maximum implied volatility
REALIZED_VOL_WINDOW = 20  # Rolling window for realized volatility calculation

# Theta parameters
DAYS_TO_EXPIRY = 30  # Days to expiry for theta calculation
THETA_SELL_THRESHOLD = -0.02  # Threshold for selling (theta decay is significant)
THETA_BUY_THRESHOLD = 0.01  # Threshold for buying (theta decay is minimal)

# Implied volatility thresholds
IV_SELL_THRESHOLD = 25  # High implied volatility threshold for selling
IV_BUY_THRESHOLD = 15  # Low implied volatility threshold for buying
