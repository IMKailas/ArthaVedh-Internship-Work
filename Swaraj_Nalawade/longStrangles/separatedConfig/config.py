# config.py

# File paths and basic settings
DATA_PATH = "NSE_NIFTY, 1D.csv"
INITIAL_BALANCE = 100000
RISK_PER_TRADE = 0.02  # 2% risk per trade

# Strategy parameters
MIN_LOOKBACK = 10  # Reduced to allow faster calculations

# Entry conditions
MIN_IMPLIED_VOLATILITY = 10  # Lowered to capture more trade opportunities
MAX_IMPLIED_VOLATILITY = 50  # Expanded to include higher IV scenarios
CALL_DELTA_TARGET = 0.25  # Broader delta target for calls
PUT_DELTA_TARGET = -0.25  # Broader delta target for puts
DELTA_TOLERANCE = 0.1  # Increased tolerance for delta deviation

# Exit conditions
PROFIT_TARGET_PERCENT = 30  # Lowered to lock profits earlier
STOP_LOSS_PERCENT = 50  # Reduced to minimize losses
MAX_HOLD_DAYS = 30  # Shortened to avoid holding for too long
IV_EXIT_THRESHOLD = 10  # Exit when IV drops below this lower level

# Position sizing
MAX_POSITION_SIZE = 10  # Increased max contracts for higher exposure
MIN_DAYS_BETWEEN_TRADES = 1  # Reduced days between trades

# Technical indicators using TA-Lib
VOLATILITY_WINDOW = 10  # Reduced lookback for faster IV calculations
VWAP_WEIGHT = 0.5  # Adjusted weights for synthetic IV
RSI_WEIGHT = 0.3
BOLL_WEIGHT = 0.2

# Output settings
LOG_FILE_PREFIX = "long_strangles_log"
TRADE_HISTORY_PREFIX = "strangle_trades"
DETAILED_OUTPUT = True  # Print detailed analysis in terminal
