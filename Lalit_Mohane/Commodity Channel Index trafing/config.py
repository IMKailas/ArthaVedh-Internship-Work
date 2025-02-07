class Config:
    def __init__(self):
        # Risk Management Parameters
        self.stop_loss_pct = 0.02  # Stop-loss as a percentage (2%)
        self.take_profit_pct = 0.05  # Take-profit as a percentage (5%)

        # Indicator Calculation Parameters
        self.sma_window = 20  # Simple Moving Average window
        self.cci_window = 20  # CCI window
        self.rsi_window = 14  # Relative Strength Index window
        self.volume_ma_window = 14  # Volume Moving Average window

        # Data File Path
        self.file_path = "NSE_NIFTY, 1 Intraday.csv"  # Path to your dataset

        # Logging Configuration
        self.log_file = "trades.log"  # Log file for storing trades and signals
        self.log_details = True  # Enable detailed logging

        # Initial Balance
        self.initial_balance = 10000  # Starting balance for trading