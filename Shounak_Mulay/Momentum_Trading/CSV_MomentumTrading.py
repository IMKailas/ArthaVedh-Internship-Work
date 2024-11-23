import pandas as pd
import os
# Load CSV data
def load_market_data(file_path):
    data = pd.read_csv(file_path)
    return data

# Momentum decision logic
def momentum_decision(row):
    volume = row['Volume']
    macd = row['MACD']
    signal_line = row['Signal']
    rsi = row['RSI']

    # Define threshold conditions
    min_volume = 300000  # Minimum volume threshold
    rsi_oversold = 60  # RSI below 30 indicates oversold condition

    # Make trading decision based on parameters
    if volume >= min_volume and macd > signal_line and rsi < rsi_oversold:
        return "Buy"  # Bullish momentum in an oversold condition

    return "Hold"  # No strong indication to buy

# Run momentum strategy
def run_momentum_strategy(data, initial_balance, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None  # Only "Buy" position is allowed
    trade_price = None  # Entry price for the current trade
    stop_loss = None  # Stop loss price
    target_profit = None  # Target profit price

    print(f"Starting Momentum Strategy with Initial Balance: {balance}\n")

    for index, row in data.iterrows():
        current_price = row['close']
        rsi = row['RSI']
        macd = row['MACD']
        signal_line = row['Signal']
        volume = row['Volume']

        # Log current market data
        print(f"Minute {index + 1}: Price={current_price:.2f}, Volume={volume}, MACD={macd:.2f}, Signal={signal_line:.2f}, RSI={rsi:.2f}")

        # Check if we should enter a position
        if position is None:
            decision = momentum_decision(row)
            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target Profit at {target_profit:.2f}")

        # If in a position, check exit conditions
        if position == "Buy":
            if current_price <= stop_loss:
                print(f"Stop Loss hit! Exiting trade at {current_price:.2f}")
                balance -= (trade_price - current_price)  # Deduct loss
                position = None
            elif current_price >= target_profit:
                print(f"Target Profit reached! Exiting trade at {current_price:.2f}")
                balance += (current_price - trade_price)  # Add profit
                position = None

        # Risk management: stop trading if balance drops significantly
        if balance <= initial_balance * 0.7:
            print(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    print(f"Final Balance: {balance:.2f}")

# Correct the file path using os.path
file_path = os.path.join(os.getcwd(), './Momentum_Trading/NSE_NIFTY, 1 Intraday.csv')

# Run strategy with data
try:
    data = load_market_data(file_path)
    initial_balance = 10000
    stop_loss_pct = 0.1
    target_profit_pct = 1
    run_momentum_strategy(data, initial_balance, stop_loss_pct, target_profit_pct)
except FileNotFoundError:
    print(f"File not found: {file_path}")
