import csv
import logging
from datetime import datetime

# Config object for strategy parameters and settings
CONFIG = {
    "lower_band_multiplier": 1.02,
    "upper_band_multiplier": 0.98,
    "RSI_buy_threshold": 45,
    "RSI_sell_threshold": 55,
    "VWAP_volume_threshold": 500000,
    "log_file": "trading_strategy.log",
    "csv_file": "NSE_NIFTY, 1 Intraday.csv"
}

# Configure logging
logging.basicConfig(
    filename=CONFIG["log_file"],
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to read CSV data
def read_csv(file_path):
    dataset = []
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convert necessary fields to float
            dataset.append({
                "time": row["time"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "VWAP": float(row["VWAP"]),
                "upper_band_1": float(row["Upper Band #1"]),
                "lower_band_1": float(row["Lower Band #1"]),
                "volume": int(row["Volume"]),
                "RSI": float(row["RSI"])
            })
    logging.info("CSV file read successfully. Total records: %d", len(dataset))
    return dataset

# Function to apply technical arbitrage strategy
def technical_arbitrage_strategy(data):
    trades = []
    for row in data:
        time = row["time"]
        close = row["close"]
        VWAP = row["VWAP"]
        upper_band_1 = row["upper_band_1"]
        lower_band_1 = row["lower_band_1"]
        RSI = row["RSI"]
        volume = row["volume"]

        # Apply relaxed strategy logic
        if close < lower_band_1 * CONFIG["lower_band_multiplier"] and RSI < CONFIG["RSI_buy_threshold"]:
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Near oversold condition"})
            logging.debug("Trade Signal: Buy | Time: %s | Price: %.2f | RSI: %.2f", time, close, RSI)
        elif close > upper_band_1 * CONFIG["upper_band_multiplier"] and RSI > CONFIG["RSI_sell_threshold"]:
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Near overbought condition"})
            logging.debug("Trade Signal: Sell | Time: %s | Price: %.2f | RSI: %.2f", time, close, RSI)
        elif close < VWAP:
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Price below VWAP"})
            logging.debug("Trade Signal: Buy | Time: %s | Price: %.2f | VWAP: %.2f", time, close, VWAP)
        elif close > VWAP:
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Price above VWAP"})
            logging.debug("Trade Signal: Sell | Time: %s | Price: %.2f | VWAP: %.2f", time, close, VWAP)
    
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
    data = read_csv(CONFIG["csv_file"])
    
    # Apply the trading strategy
    trades = technical_arbitrage_strategy(data)
    
    # Calculate profit and summary
    total_profit, trade_pairs, summary = calculate_summary(trades)
    
    # Display results
    display_summary(trades, total_profit, trade_pairs, summary)

# Run the program
if __name__ == "__main__":
    main()
