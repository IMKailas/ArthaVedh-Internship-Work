import pandas as pd
import os

# Load CSV data
def load_market_data(file_path):
    data = pd.read_csv(file_path)
    return data

# Order Flow decision logic
def order_flow_decision(row, volume_ma):
    """
    Decision logic based on VWAP, Volume, and order flow approximations.
    """
    volume = row['Volume']
    price = row['close']
    vwap = row['VWAP']

    # Buy signal: High volume and price below VWAP
    if volume > volume_ma and price < vwap:
        return "Buy"
    # Sell signal: High volume and price above VWAP
    elif volume > volume_ma and price > vwap:
        return "Sell"

    return "Hold"  # No strong order flow signal

# Run Order Flow Trading Strategy
def run_order_flow_strategy(data, initial_balance, stop_loss_pct, target_profit_pct, volume_ma):
    balance = initial_balance
    position = None  # "Buy" or "Sell" position
    trade_price = None  # Entry price for the current trade
    stop_loss = None  # Stop loss price
    target_profit = None  # Target profit price

    print(f"Starting Order Flow Trading Strategy with Initial Balance: {balance}\n")

    for index, row in data.iterrows():
        current_price = row['close']
        volume = row['Volume']
        vwap = row['VWAP']

        # Log current market data
        print(f"Minute {index + 1}: Price={current_price:.2f}, Volume={volume}, VWAP={vwap:.2f}")

        # Check if we should enter a position
        if position is None:
            decision = order_flow_decision(row, volume_ma)
            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target Profit at {target_profit:.2f}")
            elif decision == "Sell":
                position = "Sell"
                trade_price = current_price
                stop_loss = trade_price * (1 + stop_loss_pct / 100)  # Reverse stop loss for sell
                target_profit = trade_price * (1 - target_profit_pct / 100)  # Reverse target profit for sell
                print(f"Entering Sell at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target Profit at {target_profit:.2f}")

        # If in a position, check exit conditions
        if position == "Buy":
            if current_price <= stop_loss:
                print(f"Stop Loss hit! Exiting Buy trade at {current_price:.2f}")
                balance -= (trade_price - current_price)  # Deduct loss
                position = None
            elif current_price >= target_profit:
                print(f"Target Profit reached! Exiting Buy trade at {current_price:.2f}")
                balance += (current_price - trade_price)  # Add profit
                position = None

        if position == "Sell":
            if current_price >= stop_loss:
                print(f"Stop Loss hit! Exiting Sell trade at {current_price:.2f}")
                balance += (trade_price - current_price)  # Add profit (since selling short)
                position = None
            elif current_price <= target_profit:
                print(f"Target Profit reached! Exiting Sell trade at {current_price:.2f}")
                balance -= (trade_price - current_price)  # Deduct loss (since selling short)
                position = None

        # Risk management: stop trading if balance drops significantly
        if balance <= initial_balance * 0.7:
            print(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    print(f"Final Balance: {balance:.2f}")

# Correct the file path using os.path
file_path = os.path.join(os.getcwd(), './Order_Flow_Trading/NSE_NIFTY, 1 Intraday.csv')

# Define your parameters here
params = {
    'initial_balance': 10000,
    'stop_loss_pct': 0.1,
    'target_profit_pct': 1,
    'volume_ma': 1000000  # Moving average of volume (volume moving average threshold)
}

# Run strategy with data
try:
    data = load_market_data(file_path)
    run_order_flow_strategy(
        data,
        initial_balance=params['initial_balance'],
        stop_loss_pct=params['stop_loss_pct'],
        target_profit_pct=params['target_profit_pct'],
        volume_ma=params['volume_ma']
    )
except FileNotFoundError:
    print(f"File not found: {file_path}")
