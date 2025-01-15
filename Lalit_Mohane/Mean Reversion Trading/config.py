# Configuration file for Advanced Mean Reversion Strategy

config = {
    "csv_file": "NSE_NIFTY, 1D.csv",  # Path to your CSV file
    "initial_balance": 10000,  # Starting balance for the strategy
    "stop_loss_pct": 2.0,  # Stop loss percentage (2% stop loss)
    "target_profit_pct": 3.0,  # Target profit percentage (3% target profit)
    "max_loss_pct": 5.0,  # Maximum total loss percentage
    "trade_allocation": 0.1,  # Percentage of balance to allocate per trade (10% per trade)
    "max_simultaneous_trades": 3,  # Maximum number of simultaneous trades allowed
    "log_file": "trading_log.txt"  # Log file to store trade information
}
