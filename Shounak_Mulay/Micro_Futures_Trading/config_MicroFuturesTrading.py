# config.py

# Trading parameters
initial_balance = 10000  # Starting trading balance
leverage = 1            # Leverage for micro futures
stop_loss_pct = 0.1      # 0.1% stop loss
target_profit_pct = 0.1  # 0.1% target profit

# Thresholds for RSI and volume
rsi_threshold = 30  # RSI threshold for overbought/oversold
min_volume = 800    # Minimum volume threshold for considering a trade
ENABLE_DEBUG_LOGGING = True  # Enable/disable debug logging
SAVE_TRADE_HISTORY = True    # Enable/disable trade history export
