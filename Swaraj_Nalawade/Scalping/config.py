# Trading Strategy Configuration

# Initial trading parameters
INITIAL_BALANCE = 10000
STOP_LOSS_PERCENT = 0.5
TARGET_PROFIT_PERCENT = 0.5

# Volume thresholds
MIN_VOLUME = 100

# Technical indicator thresholds
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
RSI_BUY_THRESHOLD = 60
RSI_SELL_THRESHOLD = 40

# Strategy parameters
COOLDOWN_PERIODS = 5
INITIAL_LOOKBACK = 15  # Start after indicators have enough data

# File paths
CSV_FILE_PATH = "loadData.csv"

# Stochastic settings
STOCH_CROSSOVER_BUY = True  # True if K% should be > D% for buy
STOCH_CROSSOVER_SELL = True  # True if K% should be < D% for sell

# MACD settings
MACD_CROSSOVER_BUY = True  # True if MACD should be > Signal for buy
MACD_CROSSOVER_SELL = True  # True if MACD should be < Signal for sell

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Print detailed analysis for each decision
SAVE_TRADE_HISTORY = True  # Save trades to CSV file
