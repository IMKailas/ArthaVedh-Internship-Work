# config_VolatilityTrading.py

# Strategy parameters
INITIAL_BALANCE = 10000  # Starting balance
STOP_LOSS_PCT = 2.5      # Stop loss percentage
TARGET_PROFIT_PCT = 5    # Target profit percentage

# Threshold conditions for strategy
VOLUME_THRESHOLD = 375000000  # Example: significant volume
PRICE_INCREASE_THRESHOLD = 0.5  # Example: 0.5% price increase
PRICE_DECREASE_THRESHOLD = -0.5  # Example: -0.5% price decrease
HIGH_VIX_THRESHOLD = 39  # Example: high VIX threshold
ENABLE_DEBUG_LOGGING = True  # Enable/disable debug logging
SAVE_TRADE_HISTORY = True    # Enable/disable trade history export
VOL_SCORE_THRESHOLD = 1.5
ATR_THRESHOLD = 50
ADX_THRESHOLD = 25
IV_THRESHOLD = 0.2
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70