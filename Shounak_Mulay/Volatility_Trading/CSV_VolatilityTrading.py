import pandas as pd
import os
import random

# Load CSV data
def load_market_data(file_path):
    data = pd.read_csv(file_path)
    return data

# Simulate fetching VIX (Volatility Index) value
def simulate_vix():
    return round(random.uniform(10, 40), 2)  # Random VIX value between 10 and 40

# Volatility decision logic
def volume_price_decision(row, previous_row, vix):
    volume = row['Volume']
    price = row['close']
    previous_price = previous_row['close'] if previous_row is not None else price

    # Define threshold conditions
    volume_threshold = 1000  # Example: significant volume
    price_increase_threshold = 0.5  # Example: 0.5% price increase
    price_decrease_threshold = -0.5  # Example: -0.5% price decrease
    high_vix_threshold = 25  # Example: high VIX threshold

    # Calculate price change percentage
    price_change_percentage = ((price - previous_price) / previous_price) * 100 if previous_price != 0 else 0

    # Make trading decision based on volume, price change, and VIX
    if vix > high_vix_threshold and volume > volume_threshold and price_change_percentage > price_increase_threshold:
        return "Buy"
    elif vix > high_vix_threshold and volume > volume_threshold and price_change_percentage < price_decrease_threshold:
        return "Sell"

    return "Hold"  # No strong indication to trade

# Simulate price change (example logic)
def simulate_price_change(entry_price, current_price):
    # Define price fluctuation
    price_fluctuation = current_price - entry_price
    return round(current_price + price_fluctuation, 2)

# Run volume, price, and VIX strategy
def run_volatility_strategy(data, initial_balance, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None  # Track "Buy" or "Sell" positions
    trade_price = None  # Entry price for the current trade
    stop_loss = None  # Stop loss price
    target_profit = None  # Target profit price

    print(f"Starting Strategy with Initial Balance: {balance}\n")

    previous_row = None
    for index, row in data.iterrows():
        current_price = row['close']
        volume = row['Volume']
        vix = simulate_vix()  # Simulate VIX for the current minute

        # Log current market data
        print(f"Minute {index + 1}: Price={current_price:.2f}, Volume={volume}, VIX={vix}")

        # Check if we should enter a position
        if position is None:
            decision = volume_price_decision(row, previous_row, vix)
            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target Profit at {target_profit:.2f}")

            elif decision == "Sell":
                position = "Sell"
                trade_price = current_price
                stop_loss = trade_price * (1 + stop_loss_pct / 100)
                target_profit = trade_price * (1 - target_profit_pct / 100)
                print(f"Entering Sell at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target Profit at {target_profit:.2f}")

        # If in a position, check exit conditions
        if position == "Buy":
            current_price = simulate_price_change(trade_price, current_price)

            # Check for stop loss or target profit conditions
            if current_price <= stop_loss:
                print(f"Stop Loss hit on Buy! Exiting trade at {current_price:.2f}")
                balance -= (trade_price - current_price)  # Deduct loss
                position = None
            elif current_price >= target_profit:
                print(f"Target Profit reached on Buy! Exiting trade at {current_price:.2f}")
                balance += (current_price - trade_price)  # Add profit
                position = None

            print(f"Current Price: {current_price:.2f}, Balance: {balance:.2f}")

        elif position == "Sell":
            current_price = simulate_price_change(trade_price, current_price)

            # Check for stop loss or target profit conditions
            if current_price >= stop_loss:
                print(f"Stop Loss hit on Sell! Exiting trade at {current_price:.2f}")
                balance -= (current_price - trade_price)  # Deduct loss
                position = None
            elif current_price <= target_profit:
                print(f"Target Profit reached on Sell! Exiting trade at {current_price:.2f}")
                balance += (trade_price - current_price)  # Add profit
                position = None

            print(f"Current Price: {current_price:.2f}, Balance: {balance:.2f}")

        # Break if balance drops significantly (optional risk management)
        if balance <= initial_balance * 0.7:  # Example: 30% loss of initial balance stops trading
            print(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

        previous_row = row  # Update previous row for the next iteration

    print(f"Final Balance: {balance:.2f}")

# Load CSV and run strategy
file_path = os.path.join(os.getcwd(), './Momentum_Trading/NSE_NIFTY, 1 Intraday.csv')
data = load_market_data(file_path)

initial_balance = 10000  # Starting balance
stop_loss_pct = 0.5      # Stop loss percentage
target_profit_pct = 1    # Target profit percentage

run_volatility_strategy(data, initial_balance, stop_loss_pct, target_profit_pct)
