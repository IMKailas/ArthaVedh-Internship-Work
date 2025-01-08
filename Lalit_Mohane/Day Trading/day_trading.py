import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, Optional, List

# Configuration Object
CONFIG = {
    "csv_file": r"./NSE_NIFTY, 1 Intraday.csv",  # Path to the CSV file
    "initial_balance": 10000,                    # Starting balance
    "stop_loss_pct": 0.5,                        # Stop loss percentage
    "target_profit_pct": 0.5,                    # Target profit percentage
    "log_file": "trade_log.txt",                 # Log file path
    "log_details": True                          # Enable/Disable detailed logging
}

def load_market_data(csv_file):
    """Load and preprocess the CSV data"""
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'])
    return df

def get_market_data(df, current_index):
    """Get market data for the current index from DataFrame"""
    if current_index >= len(df):
        return None

    current_row = df.iloc[current_index]
    market_data = {
        "bid_price": current_row['close'],  # Closing price as bid price
        "ask_price": current_row['close'],  # Closing price as ask price
        "volume": current_row['Volume'],  # Current volume
        "volume_ma": current_row['Volume MA'],  # Moving average of volume
        "buy_orders": current_row['Volume'],  # Buy orders as total volume
        "sell_orders": current_row['Volume'],  # Sell orders as total volume
        "rsi": current_row['RSI'],  # RSI value
        "rsi_ma": current_row['RSI-based MA'],  # RSI moving average
        "macd": current_row['MACD'],  # MACD value
        "signal": current_row['Signal'],  # MACD signal line
        "upper_band": current_row['Upper Band #1'],  # Upper band of Bollinger
        "lower_band": current_row['Lower Band #1'],  # Lower band of Bollinger
        "vwap": current_row['VWAP'],  # Volume-weighted average price
        "k_percent": current_row['%K'],  # %K value for stochastic oscillator
        "d_percent": current_row['%D'],  # %D value for stochastic oscillator
        "timestamp": current_row['time']  # Timestamp
    }
    return market_data

def day_trading_decision(market_data, position=None):
    """Make a trading decision based on indicators including RSI MA and Volume MA"""
    rsi = market_data['rsi']
    rsi_ma = market_data['rsi_ma']
    macd = market_data['macd']
    signal = market_data['signal']
    volume = market_data['volume']
    volume_ma = market_data['volume_ma']
    close_price = market_data['bid_price']

    if position is None:  # No position, decide entry
        if (rsi < 40 and macd > signal) or (volume > 1.05 * volume_ma and rsi > rsi_ma):
            return "BUY", close_price
        elif (rsi > 60 and macd < signal) or (volume > 1.05 * volume_ma and rsi < rsi_ma):
            return "SELL", close_price
    else:  # Already in a position, decide exit
        if position == "BUY" and (rsi > 65 or macd < signal or rsi < rsi_ma):
            return "EXIT", close_price
        elif position == "SELL" and (rsi < 35 or macd > signal or rsi > rsi_ma):
            return "EXIT", close_price

    return "HOLD", close_price

def log_to_file(filename, message):
    """Log detailed messages to a file."""
    with open(filename, 'a') as f:
        f.write(message + '\n')

def run_day_trading_strategy(config):
    """Run the day trading strategy"""
    df = load_market_data(config["csv_file"])
    balance = config["initial_balance"]
    stop_loss_pct = config["stop_loss_pct"]
    target_profit_pct = config["target_profit_pct"]
    log_file = config["log_file"]
    log_details = config["log_details"]

    position = None
    entry_price = 0.0
    stop_loss = 0.0
    profit_target = 0.0
    trades = []

    if log_details:
        with open(log_file, 'w') as f:
            f.write("Detailed Trade Log\n")
            f.write("=" * 40 + "\n")

    for i in range(len(df)):
        market_data = get_market_data(df, i)
        if not market_data:
            break

        decision, price = day_trading_decision(market_data, position)

        if decision == "BUY":
            position = "BUY"
            entry_price = price
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
            profit_target = entry_price * (1 + target_profit_pct / 100)
            message = f"[{market_data['timestamp']}] BUY at {price:.2f}, SL: {stop_loss:.2f}, PT: {profit_target:.2f}"
            print(message)
            if log_details:
                log_to_file(log_file, message)
        elif decision == "SELL":
            position = "SELL"
            entry_price = price
            stop_loss = entry_price * (1 + stop_loss_pct / 100)
            profit_target = entry_price * (1 - target_profit_pct / 100)
            message = f"[{market_data['timestamp']}] SELL at {price:.2f}, SL: {stop_loss:.2f}, PT: {profit_target:.2f}"
            print(message)
            if log_details:
                log_to_file(log_file, message)
        elif decision == "EXIT" and position is not None:
            if position == "BUY":
                profit = price - entry_price
            elif position == "SELL":
                profit = entry_price - price

            balance += profit
            trades.append({
                'position': position,
                'entry_price': entry_price,
                'exit_price': price,
                'profit': profit,
                'timestamp': market_data['timestamp']
            })
            message = f"[{market_data['timestamp']}] EXIT {position} at {price:.2f}, Profit: {profit:.2f}, Balance: {balance:.2f}"
            print(message)
            if log_details:
                log_to_file(log_file, message)
            position = None

        if position == "BUY" and (price <= stop_loss or price >= profit_target):
            profit = price - entry_price
            balance += profit
            trades.append({
                'position': "BUY",
                'entry_price': entry_price,
                'exit_price': price,
                'profit': profit,
                'timestamp': market_data['timestamp']
            })
            message = f"[{market_data['timestamp']}] EXIT BUY at {price:.2f} due to SL/PT, Profit: {profit:.2f}, Balance: {balance:.2f}"
            print(message)
            if log_details:
                log_to_file(log_file, message)
            position = None
        elif position == "SELL" and (price >= stop_loss or price <= profit_target):
            profit = entry_price - price
            balance += profit
            trades.append({
                'position': "SELL",
                'entry_price': entry_price,
                'exit_price': price,
                'profit': profit,
                'timestamp': market_data['timestamp']
            })
            message = f"[{market_data['timestamp']}] EXIT SELL at {price:.2f} due to SL/PT, Profit: {profit:.2f}, Balance: {balance:.2f}"
            print(message)
            if log_details:
                log_to_file(log_file, message)
            position = None

    net_profit = balance - config["initial_balance"]
    print(f"\nFinal Balance: {balance:.2f}")
    print(f"Net Profit: {net_profit:.2f}")
    print(f"Total Trades: {len(trades)}")

    if log_details:
        log_to_file(log_file, f"\nFinal Balance: {balance:.2f}")
        log_to_file(log_file, f"Net Profit: {net_profit:.2f}")
        log_to_file(log_file, f"Total Trades: {len(trades)}\n")

    return balance, trades

if __name__ == "__main__":
    final_balance, trades = run_day_trading_strategy(CONFIG)
