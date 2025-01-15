# Trading Strategy Configuration

# Account Settings
INITIAL_BALANCE = 100000
RISK_PER_TRADE_PCT = 0.02  # Risk 2% per trade
MAX_DRAWDOWN_PCT = 0.10    # Stop if 10% account loss

# Fee Structure
MAKER_REBATE = 0.00025  # 0.025% rebate for providing liquidity
TAKER_FEE = 0.00075    # 0.075% fee for taking liquidity

# Entry Conditions
LONG_ENTRY = {
    'rsi_threshold': 40,
    'price_adjustment': 0.9995,  # Slightly below market for limit order
}

SHORT_ENTRY = {
    'rsi_threshold': 60,
    'price_adjustment': 1.0005,  # Slightly above market for limit order
}

# Exit Conditions
LONG_EXIT = {
    'rsi_threshold': 60,
    'stochastic_threshold': 80,
}

SHORT_EXIT = {
    'rsi_threshold': 40,
    'stochastic_threshold': 20,
}

# Logging Configuration
LOG_CONFIG = {
    'filename': 'rebate_trading_strategy.log',
    'level': 'DEBUG',
    'format': '%(asctime)s - %(levelname)s - %(message)s'
}

# Data Settings
DATA_FILE_PATH = './NSE_NIFTY_Intraday.csv'