import pandas as pd
import os
import random

# Load CSV data
def load_etf_data(file_path):
    return pd.read_csv(file_path)

# Determine volatility based on high-low range
def calculate_volatility(row):
    return row["high"] - row["low"]

# Determine market trend based on close and VWAP
def calculate_market_trend(row):
    return "up" if row["close"] > row["VWAP"] else "down"

# Trading decision based on volatility and market trend
def leveraged_etf_decision(row):
    volatility = calculate_volatility(row)
    market_trend = calculate_market_trend(row)
    high_volatility_threshold = 2.0  # Threshold for high volatility (adjust as needed)

    # Trading logic
    if volatility >= high_volatility_threshold and market_trend == "up":
        return "Buy"  # Buy in uptrend with high volatility
    elif volatility >= high_volatility_threshold and market_trend == "down":
        return "Sell"  # Sell in downtrend with high volatility

    return "Hold"

# Simulate price change based on volatility and trend
def simulate_etf_price_change(entry_price, volatility, trend):
    price_change = round(random.uniform(0.1, 2) * volatility, 2)
    if trend == "up":
        price_change *= 1.5
    elif trend == "down":
        price_change *= -1.2
    return round(entry_price + price_change, 2)

# Run the trading strategy
def run_leveraged_etf_strategy(etf_data, initial_balance, leverage, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None

    for index, row in etf_data.iterrows():
        price = row["close"]
        volatility = calculate_volatility(row)
        trend = calculate_market_trend(row)

        # Make trading decision if no open position
        if position is None:
            decision = leveraged_etf_decision(row)

            if decision == "Buy":
                position = "Buy"
                trade_price = price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy position at {trade_price} with Stop Loss at {stop_loss} and Target at {target_profit}")

            elif decision == "Sell":
                position = "Sell"
                trade_price = price
                stop_loss = trade_price * (1 + stop_loss_pct / 100)
                target_profit = trade_price * (1 - target_profit_pct / 100)
                print(f"Entering Sell position at {trade_price} with Stop Loss at {stop_loss} and Target at {target_profit}")

        # If in a position, simulate price change and check stop loss/target profit
        if position:
            current_price = simulate_etf_price_change(trade_price, volatility, trend)

            # Calculate leveraged gain or loss
            leveraged_gain_loss = (current_price - trade_price) * leverage if position == "Buy" else (trade_price - current_price) * leverage

            # Check for stop loss or target profit hit
            if position == "Buy" and current_price <= stop_loss:
                print(f"Stop Loss hit on Buy! Exiting trade at {current_price}")
                balance -= leveraged_gain_loss
                position = None
            elif position == "Buy" and current_price >= target_profit:
                print(f"Target Profit reached on Buy! Exiting trade at {current_price}")
                balance += leveraged_gain_loss
                position = None
            elif position == "Sell" and current_price >= stop_loss:
                print(f"Stop Loss hit on Sell! Exiting trade at {current_price}")
                balance -= leveraged_gain_loss
                position = None
            elif position == "Sell" and current_price <= target_profit:
                print(f"Target Profit reached on Sell! Exiting trade at {current_price}")
                balance += leveraged_gain_loss
                position = None

            # Display current trade information
            print(f"Current Price: {current_price}, Balance: {balance}")

            # Optional: stop strategy if balance drops significantly
            if balance <= initial_balance * 0.7:
                print("Balance dropped below 70% of initial value. Stopping strategy.")
                break

# Path to the CSV file
file_path = os.path.join(os.getcwd(), './Leveraged_ETF_Trading/NSE_NIFTY, 1 Intraday.csv')

# Load data from CSV
etf_data = load_etf_data(file_path)

# Run the strategy
initial_balance = 10000  # Starting balance
leverage = 3             # 3x leveraged ETF
stop_loss_pct = 5        # 5% stop loss
target_profit_pct = 10   # 10% target profit

run_leveraged_etf_strategy(etf_data, initial_balance, leverage, stop_loss_pct, target_profit_pct)
