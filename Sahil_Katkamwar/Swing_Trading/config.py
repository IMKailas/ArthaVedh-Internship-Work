# config_swing.py

# File Settings
DATA_FILE_PATH = './NSE_NIFTY, 1D.csv'
LOG_FILE_PATH = 'swing_trade.log'

# Account Settings
INITIAL_BALANCE = 10000

# Risk Management
STOP_LOSS_PCT = 2.0  # Stop loss percentage
TARGET_PROFIT_PCT = 6.0  # Target profit percentage

# Trading Conditions
RSI_OVERSOLD = 30  # RSI oversold threshold
RSI_OVERBOUGHT = 70  # RSI overbought threshold
RSI_EXIT_OVERSOLD = 30  # RSI exit oversold threshold
RSI_EXIT_OVERBOUGHT = 80  # RSI exit overbought threshold

# Position Management
STOP_LOSS_MULTIPLIER = 0.98  # Exit at 2% loss
PROFIT_TARGET_MULTIPLIER = 1.05  # Exit at 5% profit for sell

# Logging Settings
LOG_DETAILS = True  # Whether to log detailed trade information

# Market Data Columns
MARKET_DATA_COLUMNS = {
    'timestamp': 'time',
    'close': 'close',
    'volume': 'Volume',
    'volume_ma': 'Volume MA',
    'rsi': 'RSI',
    'macd': 'MACD',
    'signal': 'Signal',
    'upper_band': 'Upper Band #1',
    'lower_band': 'Lower Band #1'
}