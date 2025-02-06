class Config:
    # File paths and parameters for the strategy
    FILE_PATH = "NSE_NIFTY, 1 Intraday.csv"  # Path to the dataset
    STOP_LOSS_PCT = 0.03  # 3% stop-loss
    TAKE_PROFIT_PCT = 0.04  # 4% take-profit
    VOLUME_FACTOR = 1.2  # Volume multiplier for spike detection
    LOOKBACK_PERIOD = 3  # Lookback period for recent highs/lows
    VOLUME_MA_WINDOW = 14  # Window for volume moving average
    RSI_PERIOD = 14  # RSI calculation period
    BB_WINDOW = 20  # Bollinger Bands calculation period
    LOG_FILE = "trading_strategy.log"  # Log file for detailed logs
