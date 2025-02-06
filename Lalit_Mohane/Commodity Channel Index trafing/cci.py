import pandas as pd
import talib
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
    df = pd.read_csv(file_path)
    # Convert column names to lowercase for consistency
    df.columns = df.columns.str.lower()
    return df

# Function to calculate indicators using TA-Lib
def calculate_indicators(df, config):
    try:
        # Calculate SMA (Simple Moving Average)
        df['SMA'] = talib.SMA(df['close'], timeperiod=config.sma_window)
        
        # Calculate CCI (Commodity Channel Index)
        df['CCI'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=config.cci_window)
        
        # Calculate RSI (Relative Strength Index)
        df['RSI'] = talib.RSI(df['close'], timeperiod=config.rsi_window)
        
        # Calculate Volume Moving Average
        if 'volume' in df.columns:
            df['Volume_MA'] = talib.SMA(df['volume'], timeperiod=config.volume_ma_window)
        elif 'Volume' in df.columns:
            df['Volume_MA'] = talib.SMA(df['Volume'], timeperiod=config.volume_ma_window)
        else:
            print("Warning: Volume column not found in data")
            df['Volume_MA'] = 0  # Default value if volume data is not available
        
        return df
        
    except KeyError as e:
        print(f"Error: Column not found in data. Available columns are: {df.columns.tolist()}")
        raise
    except Exception as e:
        print(f"Error calculating indicators: {str(e)}")
        raise

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
        print(f"Buy at {buy_trade['Price']} on {buy_trade['Time']}, "
              f"Sell at {sell_trade['Price']} on {sell_trade['Time']}, "
              f"Profit: {profit}")

# Main function to execute the trading strategy
def main():
    try:
        # Create a configuration object
        config = Config()
        
        # Read dataset from CSV
        df = read_csv(config.file_path)
        
        # Calculate indicators using TA-Lib
        df = calculate_indicators(df, config)
        
        # Apply the trading strategy
        trades = cci_trading_strategy(df, config)
        
        # Calculate profit and summary
        total_profit, trade_pairs = calculate_summary(trades)
        
        # Display results
        display_summary(trades, total_profit, trade_pairs)
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()