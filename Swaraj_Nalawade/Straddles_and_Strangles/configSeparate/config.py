# config.py

# Initial balance and risk parameters
INITIAL_BALANCE = 10000
BALANCE_RISK_THRESHOLD = 0.9  # Stop trading if balance falls below 90% of initial

# Data configuration
DATA_FILE = "loadData.csv"  # Replace with your data file path

# Technical Analysis Parameters
TA_PARAMS = {
    "RSI_PERIOD": 14,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "BOLLINGER_PERIOD": 20,
    "ATR_PERIOD": 14
}

# Straddle Strategy Parameters
STRADDLE_PARAMS = {
    "BANDWIDTH_THRESHOLD": 0.0007,
    "MAX_SPREAD": 10.0,
    "MIN_VOLUME": 300000
}

# Strangle Strategy Parameters
STRANGLE_PARAMS = {
    "BANDWIDTH_THRESHOLD": 0.0007,  # Added missing parameter
    "MAX_SPREAD": 10.0,
    "MIN_VOLUME": 300000
}