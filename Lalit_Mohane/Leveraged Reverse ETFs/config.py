CONFIG = {
    "csv_file": "NSE_NIFTY, 1 Intraday.csv",  # Path to your CSV file
    "log_file": "trading_strategy.log",       # Path to the log file
    "lower_band_multiplier": 0.0015,  # Adjusted for lower volatility
    "upper_band_multiplier": 0.002,  # Adjusted for lower volatility
    "RSI_buy_threshold": 45,  # Lowered threshold
    "RSI_sell_threshold": 55,  # Lowered threshold
    "VWAP_volume_threshold": 0.8  # Reduced volume threshold
}
