# config.py
import logging

# Trading Parameters
INITIAL_BALANCE = 10000
LEVERAGE = 10  # Increased leverage for more aggressive trading
MARGIN_REQUIREMENT = 0.1  # 10% margin requirement
RISK_PER_TRADE_PCT = 0.1  # Risk 10% per trade
MAX_LOSS_PER_TRADE = 0.05  # Maximum 5% loss per trade
MAX_DRAWDOWN_PCT = 0.5  # Stop trading if 50% of initial balance is lost

# Technical Indicators
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Moving Averages
VOLUME_MA_PERIOD = 20

# Logging Configuration
LOG_FILE = 'leveraged_trading_strategy.log'
LOG_FORMAT = '%(levelname)s - %(message)s'
LOG_LEVEL = logging.DEBUG

# Data File
DATA_FILE = './NSE_NIFTY_Intraday.csv'

# Print Settings
SHOW_RECENT_TRADES = 5  # Number of recent trades to display