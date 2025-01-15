# config.py

# File paths and basic settings
DATA_PATH = "loadData.csv"
INITIAL_BALANCE = 10000
RISK_PER_TRADE = 0.02  # 2% risk per trade

# Trading parameters
MIN_LOOKBACK = 15  # Start after indicators have enough data
GAMMA_POSITION_MULTIPLIER = 25  # Reduced multiplier for gamma position

# Entry conditions
GAMMA_ENTRY_THRESHOLD = 0.015  # Increased gamma threshold
VWAP_ENTRY_THRESHOLD = 0.0005  # Tighter VWAP threshold
VEGA_ENTRY_THRESHOLD = 0.008  # Stricter vega threshold

# Exit conditions
GAMMA_EXIT_THRESHOLD = 0.008  # Low gamma threshold for exit
VEGA_EXIT_THRESHOLD = 0.012  # High vega threshold for exit
VWAP_EXIT_THRESHOLD = 0.002  # Price distance from VWAP for exit

# P&L thresholds
TAKE_PROFIT_THRESHOLD = 0.005  # Take profit at 0.5%
STOP_LOSS_THRESHOLD = -0.003  # Stop loss at -0.3%

# Hedge adjustment threshold
HEDGE_ADJUSTMENT_THRESHOLD = 0.03  # More frequent hedging

# Output file settings
LOG_FILE_PREFIX = "gamma_scalping_log"
TRADE_FILE_PREFIX = "gamma_trades"
