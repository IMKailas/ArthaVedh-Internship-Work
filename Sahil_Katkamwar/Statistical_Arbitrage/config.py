# Trading Strategy Configuration Parameters

# Account Settings
INITIAL_BALANCE = 100000
LEVERAGE = 2.0  # Increased leverage for larger position sizes
RISK_PER_TRADE_PCT = 0.05  # Increased risk per trade
TRANSACTION_COST = 0.0005  # Reduced transaction cost for larger sizes

# Position Sizing
MIN_NOTIONAL_VALUE = 100000  # Minimum notional value per leg

# Z-Score Parameters
ZSCORE_WINDOW = 20  # Window for z-score calculation
ZSCORE_ENTRY_THRESHOLD = 1.75  # Entry threshold
ZSCORE_EXIT_THRESHOLD = 0.5  # Exit threshold
ZSCORE_STOP_LOSS = 0.5  # Additional z-score movement for stop loss

# Trading Parameters
POSITION_HOLD_MINUTES = 8  # Maximum time to hold position in minutes
COOLING_OFF_MINUTES = 5  # Cooling off period after losses

# Market Condition Filters
VOLUME_THRESHOLD = 1.1  # Volume must be above MA * this value
RSI_LOWER = 40  # Lower RSI bound for stability
RSI_UPPER = 60  # Upper RSI bound for stability
TREND_PERIODS = 5  # Periods to look back for trend

# Synthetic Data Generation
SYNTHETIC_DATA = {
    'correlation': 0.92,
    'volatility_factor': 1.1,
    'volume_correlation': 0.85,
    'rsi_correlation': 0.80,
    'bank_nifty_multiplier': 3.2  # Initial BANK price relative to NIFTY
}

# Logging Settings
LOG_CONFIG = {
    'filename': 'statistical_arbitrage_strategy.log',
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s'
}

# Data Settings
DATA_FILE_PATH = './NSE_NIFTY_Intraday.csv'