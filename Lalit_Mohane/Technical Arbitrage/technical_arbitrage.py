import csv

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

        # Apply strategy logic
        if close < lower_band_1 and RSI < 40:
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Oversold condition"})
        elif close > upper_band_1 and RSI > 60:
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Overbought condition"})
        elif close < VWAP and volume > 500000:
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Price below VWAP with high volume"})
        elif close > VWAP and volume > 500000:
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Price above VWAP with high volume"})
    
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
            buy_price = None  # Reset after completing a pair

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

# Main function
def main():
    # Path to your CSV file
    file_path = "NSE_NIFTY, 1 Intraday.csv"
    
    # Read dataset from CSV
    data = read_csv(file_path)
    
    # Apply the trading strategy
    trades = technical_arbitrage_strategy(data)
    
    # Calculate profit and summary
    total_profit, trade_pairs, summary = calculate_summary(trades)
    
    # Display results
    display_summary(trades, total_profit, trade_pairs, summary)

# Run the program
if __name__ == "__main__":
    main()

import csv

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
    return dataset

# Function to apply technical arbitrage strategy
# Function to apply relaxed technical arbitrage strategy
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
        if close < lower_band_1 * 1.02 and RSI < 45:  # Slightly above lower band, higher RSI
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Near oversold condition"})
        elif close > upper_band_1 * 0.98 and RSI > 55:  # Slightly below upper band, lower RSI
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Near overbought condition"})
        elif close < VWAP:  # Removed strict volume constraint
            trades.append({"time": time, "action": "Buy", "price": close, "reason": "Price below VWAP"})
        elif close > VWAP:
            trades.append({"time": time, "action": "Sell", "price": close, "reason": "Price above VWAP"})
    
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
            buy_price = None  # Reset after completing a pair

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

# Main function
def main():
    # Path to your CSV file
    file_path = "NSE_NIFTY, 1 Intraday.csv"
    
    # Read dataset from CSV
    data = read_csv(file_path)
    
    # Apply the trading strategy
    trades = technical_arbitrage_strategy(data)
    
    # Calculate profit and summary
    total_profit, trade_pairs, summary = calculate_summary(trades)
    
    # Display results
    display_summary(trades, total_profit, trade_pairs, summary)

# Run the program
if __name__ == "__main__":
    main()