# File and Logging Configuration
LOG_FILE = 'momentum_scalping_strategy.log'
LOG_FORMAT = '%(levelname)s - %(message)s'
LOG_LEVEL = 'DEBUG'
DATA_FILE = "./NSE_NIFTY, 1 Intraday.csv"

# Initial Trading Parameters
INITIAL_BALANCE = 100000
RISK_PER_TRADE_PCT = 0.02  # 2% risk per trade

# Technical Indicator Parameters
VWAP_PERIOD = 20
VOLUME_MA_PERIOD = 20
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
ATR_PERIOD = 14

# Entry Conditions
MIN_VOLUME_RATIO = 1.2  # Minimum volume ratio for entry
MOMENTUM_LOOKBACK = 5
PRICE_MA_PERIOD = 20

# Exit Parameters
ATR_MULTIPLIER = 1.5  # For stop loss calculation
TAKE_PROFIT_RATIO = 2.0  # Risk:Reward ratio
MAX_POSITION_DURATION = 300  # Maximum position duration in seconds
MAX_DRAWDOWN_PCT = 0.20  # Maximum drawdown percentage (20%)

# Risk Management
MAX_TRADES_PER_DAY = 10
MIN_PROFIT_TARGET = 0.005  # 0.5% minimum profit target
MAX_LOSS_PER_TRADE = 0.02  # 2% maximum loss per trade