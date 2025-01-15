import pandas as pd
import logging
from config import config  # Import configurations

# Setup logging using configurations from config.py
logging.basicConfig(
    filename=config["log_file"],
    level=getattr(logging, config["logging"]["level"]),
    format=config["logging"]["format"],
    datefmt=config["logging"]["datefmt"]
)

def load_market_data(csv_file):
    """
    Load market data from a CSV file.
    """
    return pd.read_csv(csv_file)

def generate_signals(market_data, config):
    """
    Generate Buy/Sell/Hold signals based on price movement and volume.
    """
    signals = []
    for i in range(1, len(market_data)):
        price_movement = (market_data.loc[i, 'close'] - market_data.loc[i - 1, 'close']) / market_data.loc[i - 1, 'close']
        volume = market_data.loc[i, 'Volume']
        volume_ma = market_data.loc[i, 'Volume MA']
        
        if price_movement > config["price_movement_threshold"] and volume > config["volume_multiplier"] * volume_ma:
            signals.append("Buy")
        elif price_movement < -config["price_movement_threshold"] and volume > config["volume_multiplier"] * volume_ma:
            signals.append("Sell")
        else:
            signals.append("Hold")
    signals.insert(0, "Hold")  # First row has no prior data
    return signals

def execute_trades(market_data, signals, config):
    """
    Execute trades based on generated signals and calculate profit and statistics.
    """
    balance = config["initial_balance"]
    total_trades = 0
    successful_trades = 0
    profit = 0
    trade_log = []
    position = None

    for i in range(len(signals)):
        if signals[i] == "Buy" and position is None:
            # Open a position
            position = market_data.loc[i, 'close']
            trade_log.append(f"Buy at {position} on {market_data.loc[i, 'time']}")
            total_trades += 1

        elif signals[i] == "Sell" and position is not None:
            # Close the position
            sell_price = market_data.loc[i, 'close']
            trade_profit = sell_price - position
            profit += trade_profit
            balance += trade_profit
            if trade_profit > 0:
                successful_trades += 1
            trade_log.append(f"Sell at {sell_price} on {market_data.loc[i, 'time']}, Profit: {trade_profit:.2f}")
            position = None

    # Calculate statistics
    win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
    logging.info(f"Total Trades: {total_trades}")
    logging.info(f"Successful Trades: {successful_trades}")
    logging.info(f"Win Rate: {win_rate:.2f}%")
    logging.info(f"Final Balance: {balance:.2f}")
    logging.info(f"Profit: {profit:.2f}")
    return total_trades, successful_trades, win_rate, profit, balance, trade_log

def run_crypto_stock_strategy(config):
    """
    Run the crypto-stock trading strategy.
    """
    # Step 1: Load data
    market_data = load_market_data(config["csv_file"])

    # Step 2: Generate signals
    signals = generate_signals(market_data, config)

    # Step 3: Execute trades
    total_trades, successful_trades, win_rate, profit, final_balance, trade_log = execute_trades(market_data, signals, config)

    # Print results to the terminal
    print("=== Trading Strategy Summary ===")
    print(f"Total Trades Executed: {total_trades}")
    print(f"Successful Trades: {successful_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Profit: {profit:.2f}")
    print(f"Final Balance: {final_balance:.2f}")

    # Save the trade log to a file
    with open(config["log_file"], 'w') as f:
        f.write("=== Trade Log ===\n")
        for entry in trade_log:
            f.write(entry + '\n')

# Run the strategy
if __name__ == "__main__":
    run_crypto_stock_strategy(config)
