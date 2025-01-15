# config.py

# Trading Account Settings
INITIAL_BALANCE = 10000
STOP_LOSS_PCT = 0.5
TARGET_PROFIT_PCT = 0.5
BALANCE_RISK_THRESHOLD = 0.7  # Stop trading if balance drops below 70% of initial

# Market Data Simulation Parameters
PRICE_RANGE = {
    "MIN_BID": 100,
    "MAX_BID": 102,
    "MIN_ASK": 101,
    "MAX_ASK": 102
}

VOLUME_RANGE = {
    "MIN": 500,
    "MAX": 2000
}

ORDER_FLOW_RANGE = {
    "MIN": 50,
    "MAX": 200
}

# Strategy-Specific Parameters
STRADDLE_PARAMS = {
    "MAX_SPREAD": 0.5,
    "MIN_VOLUME": 800,
    "MIN_IMPLIED_VOLATILITY": 0.3,
    "IMPLIED_VOLATILITY_RANGE": {
        "MIN": 0.2,
        "MAX": 0.5
    },
    "DELTA_RANGE": {
        "MIN": -0.5,
        "MAX": 0.5
    }
}

STRANGLE_PARAMS = {
    "MAX_SPREAD": 0.5,
    "MIN_VOLUME": 500,
    "MIN_ORDER_FLOW_RATIO": 1.1
}

# Simulation Parameters
PRICE_SIMULATION = {
    "MIN_CHANGE": -0.5,
    "MAX_CHANGE": 1.0
}

UPDATE_INTERVAL = 1  # Time between market data updates (seconds)
