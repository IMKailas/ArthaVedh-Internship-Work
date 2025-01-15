# config.py
config = {
    "csv_file": "NSE_NIFTY, 1D.csv",  # Replace with your CSV path
    "initial_balance": 10000,
    "price_movement_threshold": 0.005,  # 0.5% price movement
    "volume_multiplier": 1.5,  # Volume must exceed 1.5x of Volume MA
    "log_file": "trade_log.txt",  # Log file name
    "logging": {
        "level": "INFO",  # Logging level
        "format": "%(asctime)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S"
    }
}
