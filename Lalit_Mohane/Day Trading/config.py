import os

# Define constants or load from environment variables for better security and flexibility
CONFIG = {
    "csv_file": os.path.join(os.getcwd(), "NSE_NIFTY, 1 Intraday.csv"),  # Path to the CSV file
    "initial_balance": 10000,  # Starting balance in INR
    "stop_loss_pct": 0.5,  # Stop loss percentage
    "target_profit_pct": 0.5,  # Target profit percentage
    "log_file": "trade_log.txt",  # Log file path for storing trade logs
    "log_details": True,  # Whether to log detailed information or not
    
    # Technical indicator parameters
    "rsi_period": 14,  # RSI period
    "volume_ma_period": 20,  # Volume MA period
    "macd_fast": 12,  # MACD fast period
    "macd_slow": 26,  # MACD slow period
    "macd_signal": 9,  # MACD signal period
    "bb_period": 20,  # Bollinger Bands period
    "bb_dev": 2,  # Bollinger Bands standard deviation
    "stoch_k": 14,  # Stochastic %K period
    "stoch_d": 3,  # Stochastic %D period
    "vwap_period": 14,  # VWAP period
}