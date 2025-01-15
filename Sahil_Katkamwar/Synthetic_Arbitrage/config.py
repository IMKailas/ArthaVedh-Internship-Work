# Trading Strategy Parameters
INITIAL_BALANCE = 100000
LEVERAGE = 3  # Conservative leverage for arbitrage
RISK_PER_TRADE_PCT = 0.05  # 5% risk per trade
TRANSACTION_COST = 0.001  # 0.1% transaction cost

# Market Condition Parameters
VOLUME_MA_PERIOD = 20  # Period for volume moving average
RSI_LOWER_BOUND = 30  # Lower bound for RSI stability check
RSI_UPPER_BOUND = 70  # Upper bound for RSI stability check

# Price Generation Parameters
PRICE_VOLATILITY = 0.001  # Volatility for synthetic price generation

# Risk Management Parameters
MAX_DRAWDOWN_PCT = 0.20  # Maximum drawdown percentage (20%)
POSITION_TIMEOUT = 300  # Position timeout in seconds (5 minutes)
SPREAD_CLOSURE_THRESHOLD = 0.3  # Close position when spread narrows to 30% of original

# Logging Configuration
LOG_FILE = 'synthetic_arbitrage_strategy.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'DEBUG'

# Data Configuration
DATA_FILE = './NSE_NIFTY_Intraday.csv'
DATE_COLUMN = 'time'