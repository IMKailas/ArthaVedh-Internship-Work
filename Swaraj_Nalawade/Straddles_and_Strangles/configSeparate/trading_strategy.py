import logging
import sys
import pandas as pd
import talib
import config

# Configure logging to capture both terminal output and write to a file
logfile = 'trading_strategies.log'

# Set up logger with dual handlers (file and console)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create file handler to write logs to a file
file_handler = logging.FileHandler(logfile, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create console handler to print logs to terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Use custom formatter to avoid adding extra timestamp or metadata
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Redirect stdout to the logger (so print statements are captured)
class StdoutLogger:
    def __init__(self, logger):
        self.logger = logger

    def write(self, message):
        if message.strip():  # Ignore empty lines
            self.logger.info(message)

    def flush(self):
        pass

sys.stdout = StdoutLogger(logger)

# The rest of your code remains unchanged
def load_data():
    """Load historical market data and calculate technical indicators."""
    df = pd.read_csv(config.DATA_FILE, parse_dates=['time'])
    
    # Calculate indicators
    df['RSI'] = talib.RSI(df['close'], timeperiod=config.TA_PARAMS["RSI_PERIOD"])
    df['MACD'], _, _ = talib.MACD(df['close'], fastperiod=config.TA_PARAMS["MACD_FAST"], 
                                 slowperiod=config.TA_PARAMS["MACD_SLOW"], 
                                 signalperiod=config.TA_PARAMS["MACD_SIGNAL"])
    df['Upper_BB'], df['Middle_BB'], df['Lower_BB'] = talib.BBANDS(df['close'], 
                                                           timeperiod=config.TA_PARAMS["BOLLINGER_PERIOD"])
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=config.TA_PARAMS["ATR_PERIOD"])
    df['Bandwidth'] = (df['Upper_BB'] - df['Lower_BB']) / (2 * df['Middle_BB'])  # Volatility measure
    
    df.dropna(subset=['RSI', 'MACD', 'ATR', 'Bandwidth'], inplace=True)
    return df

def execute_strategy(strategy_name, params):
    """Generalized function to execute straddle/strangle strategies"""
    df = load_data()
    balance = config.INITIAL_BALANCE
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    target_profit = None

    print(f"\n📊 **{strategy_name.capitalize()} Strategy Execution**")
    start_index = max(config.TA_PARAMS.values())

    for i in range(start_index, len(df)):
        row = df.iloc[i]
        bandwidth = row['Bandwidth']
        spread = row['high'] - row['low']
        volume = row['Volume']
        atr = row['ATR']
        current_price = row['close']

        # Entry Conditions: Bollinger Bands squeeze + sufficient volume
        if (position is None and
            bandwidth < params['BANDWIDTH_THRESHOLD'] and
            spread <= params['MAX_SPREAD'] and
            volume >= params['MIN_VOLUME']):
            
            position = strategy_name
            entry_time = row['time']
            entry_price = current_price
            stop_loss = entry_price - 2 * atr
            target_profit = entry_price + 3 * atr

            print(f"✅ Time: {entry_time} | Entered {strategy_name.capitalize()} at {entry_price:.2f} | Bandwidth: {bandwidth:.4f} | Spread: {spread:.2f} | Volume: {volume:.2f}")

        # Exit Conditions
        if position:
            if current_price <= stop_loss:
                balance -= (entry_price - current_price)
                print(f"❌ Time: {row['time']} | Stopped Out at {current_price:.2f} | Loss: {entry_price - current_price:.2f}")
                position = None

            elif current_price >= target_profit:
                balance += (current_price - entry_price)
                print(f"💰 Time: {row['time']} | Profit Booked at {current_price:.2f} | Profit: {current_price - entry_price:.2f}")
                position = None

            if balance <= config.INITIAL_BALANCE * config.BALANCE_RISK_THRESHOLD:
                print("🚨 Trading Halted: Risk Threshold Reached 🚨")
                break

    print("\n📊 **Final Results**")
    print(f"Initial Balance: ${config.INITIAL_BALANCE:,.2f}")
    print(f"Final Balance: ${balance:,.2f}")
    print(f"Net P/L: ${balance - config.INITIAL_BALANCE:,.2f}")
    print(f"Return: {((balance - config.INITIAL_BALANCE) / config.INITIAL_BALANCE * 100):.2f}%")

def run_straddle_strategy():
    execute_strategy('straddle', config.STRADDLE_PARAMS)

def run_strangle_strategy():
    execute_strategy('strangle', config.STRANGLE_PARAMS)

