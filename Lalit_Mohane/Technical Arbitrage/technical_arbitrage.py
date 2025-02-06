# technical_arbitrage.py
# trading_strategy.py

import csv
import logging
from datetime import datetime
import talib
import numpy as np
from config import Config

# Configure logging using config
Config.setup_logging()

# Function to read CSV data
def read_csv(file_path):
    dataset = {
        "time": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    }
    
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            dataset["time"].append(row["time"])
            dataset["open"].append(float(row["open"]))
            dataset["high"].append(float(row["high"]))
            dataset["low"].append(float(row["low"]))
            dataset["close"].append(float(row["close"]))
            dataset["volume"].append(int(row["Volume"]))

    logging.info("CSV file read successfully. Total records: %d", len(dataset["time"]))
    return dataset

# Function to calculate indicators using TA-Lib
def calculate_indicators(data):
    close = np.array(data["close"], dtype=float)
    high = np.array(data["high"], dtype=float)
    low = np.array(data["low"], dtype=float)
    volume = np.array(data["volume"], dtype=float)

    # Calculate Bollinger Bands
    upper_band, middle_band, lower_band = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

    # Calculate RSI
    rsi = talib.RSI(close, timeperiod=14)

    # Calculate VWAP
    typical_price = (high + low + close) / 3
    vwap = np.cumsum(typical_price * volume) / np.cumsum(volume)

    # Add calculated indicators to the dataset
    data["upper_band"] = upper_band
    data["lower_band"] = lower_band
    data["RSI"] = rsi
    data["VWAP"] = vwap

    logging.info("Indicators calculated using TA-Lib.")
    return data

# Function to apply technical arbitrage strategy
def technical_arbitrage_strategy(data):
    trades = []
    for i in range(len(data["close"])):
        time = data["time"][i]
        close = data["close"][i]
        vwap = data["VWAP"][i]
        upper_band = data["upper_band"][i]
        lower_band = data["lower_band"][i]
        rsi = data["RSI"][i]

        # Apply relaxed strategy logic
        if close < lower_band * Config.LOWER_BAND_MULTIPLIER and rsi < Config.RSI_BUY_THRESHOLD:
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Near oversold condition"})
            logging.debug("Trade Signal: Buy | Time: %s | Price: %.2f | RSI: %.2f", time, close, rsi)
        elif close > upper_band * Config.UPPER_BAND_MULTIPLIER and rsi > Config.RSI_SELL_THRESHOLD:
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Near overbought condition"})
            logging.debug("Trade Signal: Sell | Time: %s | Price: %.2f | RSI: %.2f", time, close, rsi)
        elif close < vwap:
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Price below VWAP"})
            logging.debug("Trade Signal: Buy | Time: %s | Price: %.2f | VWAP: %.2f", time, close, vwap)
        elif close > vwap:
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Price above VWAP"})
            logging.debug("Trade Signal: Sell | Time: %s | Price: %.2f | VWAP: %.2f", time, close, vwap)

    logging.info("Total trades generated: %d", len(trades))
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
    # Read dataset from CSV
    data = read_csv(Config.CSV_FILE)

    # Calculate indicators
    data = calculate_indicators(data)

    # Apply the trading strategy
    trades = technical_arbitrage_strategy(data)

    # Calculate profit and summary
    total_profit, trade_pairs, summary = calculate_summary(trades)

    # Display results
    display_summary(trades, total_profit, trade_pairs, summary)

# Run the program
if __name__ == "__main__":
    main()