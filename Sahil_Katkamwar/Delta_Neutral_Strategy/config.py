# config.py

# Trading Parameters
INITIAL_BALANCE = 10000
RISK_PER_TRADE_PCT = 0.1
MAX_LOSS_PER_TRADE = 0.02
TAKE_PROFIT_PCT = 0.03
MAX_DRAWDOWN_PCT = 0.15

# Options Parameters
MAX_GAMMA = 0.1
MAX_THETA = 50

# Technical Indicators
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Moving Averages
VOLUME_MA_PERIOD = 20
IV_MA_PERIOD = 20
GAMMA_MA_PERIOD = 20

# Options Data Parameters
RISK_FREE_RATE = 0.05
DAYS_TO_EXPIRY = 5
IV_HV_RATIO = 1.1  # IV is typically 10% higher than HV
PUT_CALL_RATIO_THRESHOLD = 1.2
DELTA_IMBALANCE_THRESHOLD = 0.15
DELTA_NEUTRAL_THRESHOLD = 0.05
IV_CRUSH_THRESHOLD = 0.8

# Historical Volatility
HV_WINDOW = 20
TRADING_DAYS = 252  # Number of trading days in a year

# Logging Configuration
LOG_FILE = 'delta_neutral_strategy.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Data File
DATA_FILE = './NSE_NIFTY_Intraday.csv'