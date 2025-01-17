
# config.py

# File Settings
DATA_FILE = r"C:\assignement\sem5\Internship\Straddles_and_Strangles\loadData.csv"  # Your input CSV file name
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"  # Date format in CSV

# Trading Account Settings
INITIAL_BALANCE = 10000
STOP_LOSS_PCT = 0.5
TARGET_PROFIT_PCT = 0.5
BALANCE_RISK_THRESHOLD = 0.7  # Stop trading if balance drops below 70% of initial

# Strategy Parameters
STRADDLE_PARAMS = {
    "MAX_SPREAD": 0.5,
    "MIN_VOLUME": 800,
    "MIN_IMPLIED_VOLATILITY": 30,  # RSI can be used as a volatility indicator
    "RSI_OVERSOLD": 30,
    "RSI_OVERBOUGHT": 70
}

STRANGLE_PARAMS = {
    "MAX_SPREAD": 0.5,
    "MIN_VOLUME": 500,
    "MIN_ORDER_FLOW_RATIO": 1.1,
    "VOLUME_MA_MULTIPLIER": 1.2  # Volume should be 20% above MA for signal
}

# Technical Indicators
MOVING_AVERAGE_PERIOD = 20  # For Volume MA
RSI_PERIOD = 14

# Update Interval (in seconds)
UPDATE_INTERVAL = 1
