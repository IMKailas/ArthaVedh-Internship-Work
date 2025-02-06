import pandas as pd
import numpy as np
from datetime import datetime
import logging
import talib
from config import *

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def calculate_theta(data, days_to_expiry):
    """Calculate theta decay."""
    data['Theta'] = -np.log(data['close'] / data['close'].shift(1)) / days_to_expiry
    return data

def calculate_indicators(data):
    """Calculate indicators using TA-Lib."""
    data['RSI'] = talib.RSI(data['close'], timeperiod=14)
    data['MACD'], data['Signal'], data['Histogram'] = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    data['ATR'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    data['Implied_Vol'] = talib.STDDEV(data['close'], timeperiod=REALIZED_VOL_WINDOW) * 100
    return data

def theta_decay_trading_decision(data):
    """Make trading decisions based on theta and implied volatility."""
    balance = INITIAL_BALANCE
    trade_log = []
    position = None  # 'long' or 'short'
    entry_price = None

    for idx, row in data.iterrows():
        if np.isnan(row['Theta']) or np.isnan(row['Implied_Vol']):
            continue

        # Decision parameters
        theta_signal = row['Theta']
        implied_vol_signal = row['Implied_Vol']

        # Entry conditions
        if position is None:
            if theta_signal < THETA_SELL_THRESHOLD and implied_vol_signal > IV_SELL_THRESHOLD:
                position = 'short'
                entry_price = row['close']
                trade_log.append(f"SELL at {entry_price:.2f}")
                logging.info(f"SELL at {entry_price:.2f}")

            elif theta_signal > THETA_BUY_THRESHOLD and implied_vol_signal < IV_BUY_THRESHOLD:
                position = 'long'
                entry_price = row['close']
                trade_log.append(f"BUY at {entry_price:.2f}")
                logging.info(f"BUY at {entry_price:.2f}")

        # Exit conditions
        elif position == 'long':
            if row['close'] >= entry_price * (1 + PROFIT_TARGET) or row['close'] <= entry_price * (1 - STOP_LOSS):
                profit = (row['close'] - entry_price) * TRADE_SIZE
                balance += profit
                trade_log.append(f"EXIT LONG at {row['close']:.2f}, Profit: {profit:.2f}")
                logging.info(f"EXIT LONG at {row['close']:.2f}, Profit: {profit:.2f}")
                position = None

        elif position == 'short':
            if row['close'] <= entry_price * (1 - PROFIT_TARGET) or row['close'] >= entry_price * (1 + STOP_LOSS):
                profit = (entry_price - row['close']) * TRADE_SIZE
                balance += profit
                trade_log.append(f"EXIT SHORT at {row['close']:.2f}, Profit: {profit:.2f}")
                logging.info(f"EXIT SHORT at {row['close']:.2f}, Profit: {profit:.2f}")
                position = None

    return balance, trade_log

def summarize_trades(trade_log, initial_balance, final_balance):
    """Print and log trade summary."""
    total_trades = len([log for log in trade_log if 'EXIT' in log])
    win_trades = len([log for log in trade_log if 'Profit' in log and 'Profit: ' in log and float(log.split('Profit: ')[1]) > 0])
    loss_trades = total_trades - win_trades
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    summary = (
        f"Trade Summary:\n"
        f"Initial Balance: {initial_balance:.2f}\n"
        f"Final Balance: {final_balance:.2f}\n"
        f"Total Trades: {total_trades}\n"
        f"Winning Trades: {win_trades}\n"
        f"Losing Trades: {loss_trades}\n"
        f"Win Rate: {win_rate:.2f}%\n"
    )

    print(summary)
    logging.info(summary)

# Main script execution
if __name__ == "__main__":
    # Load and preprocess data
    data = pd.read_csv("NSE_NIFTY, 1D.csv", usecols=['time', 'open', 'high', 'low', 'close', 'Volume'])
    data = calculate_theta(data, DAYS_TO_EXPIRY)
    data = calculate_indicators(data)

    # Execute trades
    final_balance, trade_log = theta_decay_trading_decision(data)

    # Summarize results
    summarize_trades(trade_log, INITIAL_BALANCE, final_balance)

    # Save detailed log
    with open(LOG_FILE, 'a') as f:
        f.write("\n".join(trade_log))
        f.write("\n")
