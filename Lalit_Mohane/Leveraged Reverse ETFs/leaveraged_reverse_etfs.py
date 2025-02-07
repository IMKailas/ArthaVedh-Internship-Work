# Import necessary libraries
import csv
import logging
import talib
import numpy as np
from datetime import datetime
from config import CONFIG

# Configure logging
logging.basicConfig(
    filename=CONFIG["log_file"],
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to read CSV data
def read_csv(file_path):
    dataset = []
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                dataset.append({
                    "time": row["time"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["Volume"])
                })
        logging.info("CSV file read successfully. Total records: %d", len(dataset))
    except Exception as e:
        logging.error("Error reading CSV: %s", str(e))
        raise
    return dataset

# Function to calculate indicators using TA-Lib
def calculate_indicators(data):
    closes = np.array([row["close"] for row in data], dtype=float)
    highs = np.array([row["high"] for row in data], dtype=float)
    lows = np.array([row["low"] for row in data], dtype=float)
    volumes = np.array([row["volume"] for row in data], dtype=float)

    # Calculate RSI
    rsi = talib.RSI(closes, timeperiod=14)

    # Calculate Bollinger Bands
    upper_band, middle_band, lower_band = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

    # Calculate Volume Moving Average
    volume_ma = talib.SMA(volumes, timeperiod=14)

    # Calculate Beta using Linear Regression Slope
    beta = talib.LINEARREG_SLOPE(closes, timeperiod=14)

    # Add indicators to the data rows
    for i, row in enumerate(data):
        row["RSI"] = rsi[i] if not np.isnan(rsi[i]) else 0
        row["upper_band"] = upper_band[i] if not np.isnan(upper_band[i]) else 0
        row["lower_band"] = lower_band[i] if not np.isnan(lower_band[i]) else 0
        row["volume_MA"] = volume_ma[i] if not np.isnan(volume_ma[i]) else 0
        row["beta"] = beta[i] if not np.isnan(beta[i]) else 0

    logging.info("Indicators calculated successfully using TA-Lib.")
    return data

# Function to apply the leveraged ETF strategy
def leveraged_reverse_etfs_strategy(data):
    trades = []
    for row in data:
        beta = row["beta"]  # Use the beta calculated by TA-Lib
        volatility = (row["high"] - row["low"]) / row["low"]  # Calculate intraday volatility
        volume_ratio = row["volume"] / row["volume_MA"] if row["volume_MA"] > 0 else 0  # Calculate volume ratio

        # Relaxed decision-making conditions
        if (volatility > CONFIG["lower_band_multiplier"] * 0.5 and
            row["RSI"] < CONFIG["RSI_buy_threshold"] + 10 and
            volume_ratio > CONFIG["VWAP_volume_threshold"] * 0.5):
            trades.append({"action": "Buy", "price": row["close"], "time": row["time"], "beta": beta})
            logging.debug("Buy Signal: Time: %s, Price: %.2f, Beta: %.2f, Volatility: %.4f, Volume Ratio: %.2f",
                          row["time"], row["close"], beta, volatility, volume_ratio)

        elif (volatility > CONFIG["upper_band_multiplier"] * 0.5 and
              row["RSI"] > CONFIG["RSI_sell_threshold"] - 10 and
              volume_ratio > CONFIG["VWAP_volume_threshold"] * 0.5):
            trades.append({"action": "Sell", "price": row["close"], "time": row["time"], "beta": beta})
            logging.debug("Sell Signal: Time: %s, Price: %.2f, Beta: %.2f, Volatility: %.4f, Volume Ratio: %.2f",
                          row["time"], row["close"], beta, volatility, volume_ratio)

    return trades

# Function to calculate profit and summary
def calculate_summary(trades):
    total_profit = 0
    trade_pairs = []
    buy_price = None
    summary = {
        "total_trades": 0,
        "profitable_trades": 0,
        "loss_trades": 0
    }

    for trade in trades:
        if trade["action"] == "Buy" and buy_price is None:
            buy_price = trade["price"]
        elif trade["action"] == "Sell" and buy_price is not None:
            sell_price = trade["price"]
            profit = sell_price - buy_price
            total_profit += profit
            trade_pairs.append((buy_price, sell_price, profit))
            summary["total_trades"] += 1
            if profit > 0:
                summary["profitable_trades"] += 1
            else:
                summary["loss_trades"] += 1
            logging.debug("Trade Pair: Bought at %.2f, Sold at %.2f, Profit: %.2f", buy_price, sell_price, profit)
            buy_price = None  # Reset after completing a pair

    logging.info("Total Profit: %.2f", total_profit)
    return total_profit, trade_pairs, summary

# Function to display trade results and summary
def display_summary(trades, total_profit, trade_pairs, summary):
    print("\nTrade Details:")
    for i, (buy, sell, profit) in enumerate(trade_pairs, start=1):
        print(f"Trade {i}: Bought at {buy}, Sold at {sell}, Profit: {profit:.2f}")

    print("\nSummary:")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Profitable Trades: {summary['profitable_trades']}")
    print(f"Loss Trades: {summary['loss_trades']}")
    print(f"Total Profit: {total_profit:.2f}")
    logging.info("Summary displayed successfully.")

# Main function
def main():
    try:
        # Read dataset from CSV
        data = read_csv(CONFIG["csv_file"])

        # Calculate indicators using TA-Lib
        data = calculate_indicators(data)

        # Apply the trading strategy
        trades = leveraged_reverse_etfs_strategy(data)

        # Calculate profit and summary
        total_profit, trade_pairs, summary = calculate_summary(trades)

        # Display results
        display_summary(trades, total_profit, trade_pairs, summary)
    except Exception as e:
        logging.error("Error in main function: %s", str(e))
        print("An error occurred. Check the logs for more details.")

# Run the program
if __name__ == "__main__":
    main()
