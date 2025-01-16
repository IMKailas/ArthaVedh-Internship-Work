# config.py

# Trading parameters
initial_balance = 10000  # Starting trading balance
stop_loss_pct = 0.1      # 0.1% stop loss
target_profit_pct = 1    # 1% target profit

# Thresholds for RSI, MACD, and volume
min_volume = 300000      # Minimum volume threshold
rsi_oversold = 60        # RSI value below which is considered oversold

ENABLE_DEBUG_LOGGING = True  # Enable/disable debug logging
SAVE_TRADE_HISTORY = True    # Enable/disable trade history export