import pandas as pd
import numpy as np
import logging
from config import Config

# Configure logging to write to a file
logging.basicConfig(
    filename=Config().log_file, 
    level=logging.INFO, 
    format='%(asctime)s - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Function to read CSV and load data
def read_csv(file_path):
    return pd.read_csv(file_path)

# Function to calculate SMA (Simple Moving Average)
def calculate_sma(df, window=14):
    df['SMA'] = df['close'].rolling(window=window).mean()
    return df

# Function to calculate CCI (Commodity Channel Index)
def calculate_cci(df, window=14):
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['SMA_Typical_Price'] = df['Typical_Price'].rolling(window=window).mean()
    df['Mean_Deviation'] = df['Typical_Price'].rolling(window=window).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    df['CCI'] = (df['Typical_Price'] - df['SMA_Typical_Price']) / (0.015 * df['Mean_Deviation'])
    return df

# Function to calculate RSI (Relative Strength Index)
def calculate_rsi(df, window=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# Function to calculate Volume MA (Volume Moving Average)
def calculate_volume_ma(df, window=14):
    df['Volume_MA'] = df['Volume'].rolling(window=window).mean()
    return df

# Trading strategy using CCI, RSI, and Volume for confirmation
def cci_trading_strategy(df, config):
    trades = []
    in_position = False
    buy_price = None
    
    for index, row in df.iterrows():
        # Buy condition: CCI > 100, Close > SMA, RSI between 45-55
        if row['CCI'] > 100 and row['close'] > row['SMA'] and 45 < row['RSI'] < 55 and not in_position:
            buy_price = row['close']
            trade = {'Time': row['time'], 'Action': 'Buy', 'Price': buy_price}
            trades.append(trade)
            logging.info(f"Buy signal: {trade}")
            in_position = True
        
        if in_position:
            # Stop-loss or Take-profit conditions
            if row['close'] <= buy_price * (1 - config.stop_loss_pct):
                trade = {'Time': row['time'], 'Action': 'Sell (Stop-Loss)', 'Price': row['close']}
                trades.append(trade)
                logging.info(f"Stop-Loss triggered: {trade}")
                in_position = False
            elif row['close'] >= buy_price * (1 + config.take_profit_pct):
                trade = {'Time': row['time'], 'Action': 'Sell (Take-Profit)', 'Price': row['close']}
                trades.append(trade)
                logging.info(f"Take-Profit triggered: {trade}")
                in_position = False
            elif row['CCI'] < -100 and row['close'] < row['SMA']:
                trade = {'Time': row['time'], 'Action': 'Sell', 'Price': row['close']}
                trades.append(trade)
                logging.info(f"Sell signal: {trade}")
                in_position = False
    
    return trades

# Function to calculate total profit and summary of trades
def calculate_summary(trades):
    total_profit = 0
    trade_pairs = []
    
    for i in range(0, len(trades), 2):  # Assuming Buy and Sell come in pairs
        if i + 1 < len(trades):
            buy_trade = trades[i]
            sell_trade = trades[i + 1]
            profit = sell_trade['Price'] - buy_trade['Price']
            total_profit += profit
            trade_pairs.append((buy_trade, sell_trade, profit))
    
    return total_profit, trade_pairs

# Function to display summary of trades and profit
def display_summary(trades, total_profit, trade_pairs):
    print(f"Total Profit: {total_profit}")
    for buy_trade, sell_trade, profit in trade_pairs:
        print(f"Buy at {buy_trade['Price']} on {buy_trade['Time']}, Sell at {sell_trade['Price']} on {sell_trade['Time']}, Profit: {profit}")

# Main function to execute the trading strategy
def main():
    # Create a configuration object
    config = Config()
    
    # Read dataset from CSV
    df = read_csv(config.file_path)
    
    # Calculate the SMA (Simple Moving Average)
    df = calculate_sma(df, window=config.sma_window)
    
    # Calculate the CCI (Commodity Channel Index)
    df = calculate_cci(df, window=config.cci_window)
    
    # Calculate the RSI (Relative Strength Index)
    df = calculate_rsi(df, window=config.rsi_window)
    
    # Calculate Volume Moving Average
    df = calculate_volume_ma(df, window=config.volume_ma_window)
    
    # Apply the trading strategy
    trades = cci_trading_strategy(df, config)
    
    # Calculate profit and summary
    total_profit, trade_pairs = calculate_summary(trades)
    
    # Display results
    display_summary(trades, total_profit, trade_pairs)

if __name__ == "__main__":
    main()
