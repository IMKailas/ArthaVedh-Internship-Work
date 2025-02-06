import pandas as pd
import talib
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, List
from config import CONFIG

def calculate_indicators(df):
    """Calculate technical indicators using TA-Lib"""
    # RSI and RSI MA
    df['RSI'] = talib.RSI(df['close'], timeperiod=CONFIG['rsi_period'])
    df['RSI-based MA'] = talib.SMA(df['RSI'], timeperiod=CONFIG['rsi_period'])
    
    # Volume MA
    df['Volume MA'] = talib.SMA(df['Volume'], timeperiod=CONFIG['volume_ma_period'])
    
    # MACD
    df['MACD'], df['Signal'], _ = talib.MACD(df['close'], 
                                            fastperiod=CONFIG['macd_fast'],
                                            slowperiod=CONFIG['macd_slow'],
                                            signalperiod=CONFIG['macd_signal'])
    
    # Bollinger Bands
    df['Upper Band #1'], middle, df['Lower Band #1'] = talib.BBANDS(
        df['close'],
        timeperiod=CONFIG['bb_period'],
        nbdevup=CONFIG['bb_dev'],
        nbdevdn=CONFIG['bb_dev']
    )
    
    # Stochastic Oscillator
    df['%K'], df['%D'] = talib.STOCH(df['high'], 
                                    df['low'], 
                                    df['close'],
                                    fastk_period=CONFIG['stoch_k'],
                                    slowk_period=3,
                                    slowk_matype=0,
                                    slowd_period=CONFIG['stoch_d'],
                                    slowd_matype=0)
    
    # VWAP (approximation using SMA of price * volume)
    df['VWAP'] = talib.SMA(df['close'] * df['Volume'], timeperiod=CONFIG['vwap_period']) / \
                 talib.SMA(df['Volume'], timeperiod=CONFIG['vwap_period'])
    
    return df

def load_market_data(csv_file):
    """Load and preprocess the CSV data"""
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'])
    df = calculate_indicators(df)  # Calculate indicators using TA-Lib
    return df

def get_market_data(df, current_index):
    """Get market data for the current index from DataFrame"""
    if current_index >= len(df):
        return None

    current_row = df.iloc[current_index]
    market_data = {
        "bid_price": current_row['close'],
        "ask_price": current_row['close'],
        "volume": current_row['Volume'],
        "volume_ma": current_row['Volume MA'],
        "buy_orders": current_row['Volume'],
        "sell_orders": current_row['Volume'],
        "rsi": current_row['RSI'],
        "rsi_ma": current_row['RSI-based MA'],
        "macd": current_row['MACD'],
        "signal": current_row['Signal'],
        "upper_band": current_row['Upper Band #1'],
        "lower_band": current_row['Lower Band #1'],
        "vwap": current_row['VWAP'],
        "k_percent": current_row['%K'],
        "d_percent": current_row['%D'],
        "timestamp": current_row['time']
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
    try:
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

            # Check stop loss and profit target
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

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    final_balance, trades = run_day_trading_strategy(CONFIG)