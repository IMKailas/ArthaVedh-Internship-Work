import pandas as pd
import numpy as np
import logging
from config import Config

# Setup logging
logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger()

def read_csv(file_path):
    """Function to read CSV and load data."""
    logger.info(f"Reading CSV file: {file_path}")
    return pd.read_csv(file_path)

def calculate_volume_ma(df, window):
    """Function to calculate Volume Moving Average."""
    logger.info(f"Calculating Volume Moving Average with window: {window}")
    df['Volume_MA'] = df['Volume'].rolling(window=window).mean()
    return df

def calculate_summary(trades):
    """Function to calculate summary of trades."""
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

def display_summary(trades, total_profit, trade_pairs):
    """Function to display trade summary and profits."""
    print(f"Total Profit: {total_profit:.2f}")
    print(f"Number of Trades: {len(trade_pairs)}")
    for buy_trade, sell_trade, profit in trade_pairs:
        print(f"Buy at {buy_trade['Price']} on {buy_trade['Time']}, "
              f"Sell at {sell_trade['Price']} on {sell_trade['Time']}, "
              f"Profit: {profit:.2f}")

def penny_stock_trading_strategy(df, config):
    """Penny stock trading strategy based on volume and price patterns."""
    trades = []
    in_position = False
    buy_price = None

    for index, row in df.iterrows():
        if index < config.LOOKBACK_PERIOD:
            continue

        recent_high = df['high'][index - config.LOOKBACK_PERIOD:index].max()
        recent_low = df['low'][index - config.LOOKBACK_PERIOD:index].min()

        logger.debug(f"Index: {index}, Recent High: {recent_high}, Recent Low: {recent_low}, Volume: {row['Volume']}, Volume_MA: {row['Volume_MA']}")

        if row['Volume'] > config.VOLUME_FACTOR * row['Volume_MA'] and row['close'] > recent_high and not in_position:
            buy_price = row['close']
            trades.append({'Time': row['time'], 'Action': 'Buy', 'Price': buy_price})
            logger.info(f"Buy Signal: Time={row['time']}, Price={buy_price}, Volume={row['Volume']}")
            in_position = True

        if in_position:
            if row['close'] <= buy_price * (1 - config.STOP_LOSS_PCT):
                trades.append({'Time': row['time'], 'Action': 'Sell (Stop-Loss)', 'Price': row['close']})
                logger.info(f"Sell Signal (Stop-Loss): Time={row['time']}, Price={row['close']}")
                in_position = False
            elif row['close'] >= buy_price * (1 + config.TAKE_PROFIT_PCT):
                trades.append({'Time': row['time'], 'Action': 'Sell (Take-Profit)', 'Price': row['close']})
                logger.info(f"Sell Signal (Take-Profit): Time={row['time']}, Price={row['close']}")
                in_position = False
            elif row['close'] < recent_low or row['Volume'] < row['Volume_MA']:
                trades.append({'Time': row['time'], 'Action': 'Sell', 'Price': row['close']})
                logger.info(f"Sell Signal: Time={row['time']}, Price={row['close']}")
                in_position = False

    return trades

def main():
    """Main function to execute the penny stock trading strategy."""
    logger.info("Starting penny stock trading strategy...")

    # Read dataset from CSV
    df = read_csv(Config.FILE_PATH)

    # Calculate Volume Moving Average
    df = calculate_volume_ma(df, Config.VOLUME_MA_WINDOW)

    # Apply the trading strategy
    trades = penny_stock_trading_strategy(df, Config)

    # Calculate profit and summary
    total_profit, trade_pairs = calculate_summary(trades)

    # Display results
    display_summary(trades, total_profit, trade_pairs)

    logger.info(f"Trading strategy completed. Total Profit: {total_profit:.2f}")
    logger.info(f"Number of Trades: {len(trade_pairs)}")

if __name__ == "__main__":
    main()
