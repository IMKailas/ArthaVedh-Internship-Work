import os

# Get the directory containing the config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    # File and paths
    "csv_file": os.path.join(BASE_DIR, "data", "NSE_NIFTY, 1D.csv"), 
    "log_file": os.path.join(BASE_DIR, "logs", "trade_log.txt"),
    
    # Trading parameters
    "initial_balance": 10000,  # Starting balance in INR
    "position_size": 0.95,     # Percentage of balance to use per trade
    "stop_loss_pct": 0.5,      # Stop loss percentage
    "target_profit_pct": 0.5,  # Target profit percentage
    
    # Technical indicator parameters
    "indicators": {
        "rsi": {
            "period": 14,
            "overbought": 70,
            "oversold": 30
        },
        "macd": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        },
        "bollinger": {
            "period": 20,
            "std_dev": 2
        },
        "stochastic": {
            "k_period": 14,
            "d_period": 3,
            "slowing": 3
        },
        "vwap": {
            "period": 14
        }
    },
    
    # Logging configuration
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S"
    },
    
    # Trading thresholds
    "price_movement_threshold": 0.001,  # 0.1% price movement
    "volume_multiplier": 1.5,          # Volume should be 1.5x the average
}

# Create necessary directories
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)