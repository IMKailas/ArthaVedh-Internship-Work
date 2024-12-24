import pandas as pd
import numpy as np

# Adjustable parameters
stop_loss_pct = 0.03  # 3% stop-loss
take_profit_pct = 0.04  # 4% take-profit
volume_factor = 1.2  # Volume multiplier for spike detection
lookback_period = 3  # Lookback period for recent highs/lows

# Function to read CSV and load data
def read_csv(file_path):
    return pd.read_csv(file_path)

# Function to calculate Volume Moving Average
def calculate_volume_ma(df, window=14):
    df['Volume_MA'] = df['Volume'].rolling(window=window).mean()
    return df

# Function to calculate summary of trades
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

# Function to display trade summary and profits
def display_summary(trades, total_profit, trade_pairs):
    print(f"Total Profit: {total_profit:.2f}")
    print(f"Number of Trades: {len(trade_pairs)}")
    for buy_trade, sell_trade, profit in trade_pairs:
        print(f"Buy at {buy_trade['Price']} on {buy_trade['Time']}, "
              f"Sell at {sell_trade['Price']} on {sell_trade['Time']}, "
              f"Profit: {profit:.2f}")

# Penny stock trading strategy based on volume and price patterns
def penny_stock_trading_strategy(df, stop_loss_pct, take_profit_pct, volume_factor, lookback_period):
    trades = []
    in_position = False
    buy_price = None

    for index, row in df.iterrows():
        if index < lookback_period:  # Skip rows where there's insufficient data for lookback
            continue

        # Calculate recent highs and lows for the lookback period
        recent_high = df['high'][index - lookback_period:index].max()
        recent_low = df['low'][index - lookback_period:index].min()

        # Debug: Print conditions being checked
        # print(f"Index: {index}, Recent High: {recent_high}, Recent Low: {recent_low}, Volume: {row['Volume']}, Volume_MA: {row['Volume_MA']}")

        # Buy condition: Volume spike and breakout above recent high
        if row['Volume'] > volume_factor * row['Volume_MA'] and row['close'] > recent_high and not in_position:
            buy_price = row['close']
            trades.append({'Time': row['time'], 'Action': 'Buy', 'Price': buy_price})
            print(f"Buy Signal: Time={row['time']}, Price={buy_price}, Volume={row['Volume']}")
            in_position = True

        # Sell conditions: Price drop below recent low or volume drop or stop-loss/take-profit
        if in_position:
            # Stop-loss or Take-profit
            if row['close'] <= buy_price * (1 - stop_loss_pct):
                trades.append({'Time': row['time'], 'Action': 'Sell (Stop-Loss)', 'Price': row['close']})
                print(f"Sell Signal (Stop-Loss): Time={row['time']}, Price={row['close']}")
                in_position = False
            elif row['close'] >= buy_price * (1 + take_profit_pct):
                trades.append({'Time': row['time'], 'Action': 'Sell (Take-Profit)', 'Price': row['close']})
                print(f"Sell Signal (Take-Profit): Time={row['time']}, Price={row['close']}")
                in_position = False
            # Regular sell condition based on price or volume
            elif row['close'] < recent_low or row['Volume'] < row['Volume_MA']:
                trades.append({'Time': row['time'], 'Action': 'Sell', 'Price': row['close']})
                print(f"Sell Signal: Time={row['time']}, Price={row['close']}")
                in_position = False

    return trades

# Main function to execute the penny stock trading strategy
def main():
    file_path = "NSE_NIFTY, 1 Intraday.csv"  # Path to your dataset

    # Read dataset from CSV
    df = read_csv(file_path)

    # Calculate Volume Moving Average
    df = calculate_volume_ma(df, window=14)

    # Apply the trading strategy
    trades = penny_stock_trading_strategy(df, stop_loss_pct, take_profit_pct, volume_factor, lookback_period)

    # Calculate profit and summary
    total_profit, trade_pairs = calculate_summary(trades)

    # Display results
    display_summary(trades, total_profit, trade_pairs)

if __name__ == "__main__":
    main()
