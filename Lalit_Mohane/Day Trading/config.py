# config.py

import os

# Define constants or load from environment variables for better security and flexibility
CONFIG = {
    "csv_file": os.path.join(os.getcwd(), "NSE_NIFTY, 1 Intraday.csv"),  # Path to the CSV file (change as needed)
    "initial_balance": 10000,  # Starting balance in INR
    "stop_loss_pct": 0.5,  # Stop loss percentage
    "target_profit_pct": 0.5,  # Target profit percentage
    "log_file": "trade_log.txt",  # Log file path for storing trade logs
    "log_details": True,  # Whether to log detailed information or not (True/False)
}
