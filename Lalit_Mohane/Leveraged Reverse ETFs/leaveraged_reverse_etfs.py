import csv
import logging
import random
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
                    "VWAP": float(row["VWAP"]),
                    "upper_band_1": float(row["Upper Band #1"]),
                    "lower_band_1": float(row["Lower Band #1"]),
                    "volume": int(row["Volume"]),
                    "RSI": float(row["RSI"]),
                    "volume_MA": float(row["Volume MA"])
                })
        logging.info("CSV file read successfully. Total records: %d", len(dataset))
    except Exception as e:
        logging.error("Error reading CSV: %s", str(e))
        raise
    return dataset

# Function to calculate Beta (simulated for this example)
def calculate_beta():
    return round(random.uniform(0.8, 1.5), 2)  # Simulating Beta between 0.8 and 1.5

# Function to apply the leveraged ETF strategy
# Function to apply the leveraged ETF strategy with relaxed conditions
# Function to apply the leveraged ETF strategy
def leveraged_reverse_etfs_strategy(data):
    trades = []
    for row in data:
        beta = calculate_beta()  # Simulate Beta value
        volatility = (row["high"] - row["low"]) / row["low"]  # Calculate intraday volatility
        volume_ratio = row["volume"] / row["volume_MA"]  # Calculate volume ratio
        
        # Relaxed decision-making conditions
        if (volatility > CONFIG["lower_band_multiplier"] * 0.5 and  # Reduced threshold
            row["RSI"] < CONFIG["RSI_buy_threshold"] + 10 and  # Increased threshold
            volume_ratio > CONFIG["VWAP_volume_threshold"] * 0.5):  # Relaxed condition
            trades.append({"action": "Buy", "price": row["close"], "time": row["time"], "beta": beta})
            logging.debug("Buy Signal: Time: %s, Price: %.2f, Beta: %.2f, Volatility: %.4f, Volume Ratio: %.2f",
                          row["time"], row["close"], beta, volatility, volume_ratio)
        
        elif (volatility > CONFIG["upper_band_multiplier"] * 0.5 and  # Reduced threshold
              row["RSI"] > CONFIG["RSI_sell_threshold"] - 10 and  # Increased threshold
              volume_ratio > CONFIG["VWAP_volume_threshold"] * 0.5):  # Relaxed condition
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
