import pandas as pd
import os

# Load CSV data
def load_market_data(file_path):
    data = pd.read_csv(file_path)
    return data

# Smart order routing decision logic based on volume and VWAP
def routing_decision(row, volume_ma):
    volume = row['Volume']
    vwap = row['VWAP']

    # Routing decision based on volume and price (VWAP)
    if volume > volume_ma and row['close'] < vwap:  # Bullish signal based on volume and price below VWAP
        return "Buy_Route"  # Route to high-liquidity exchange for buying
    elif volume > volume_ma and row['close'] > vwap:  # Bearish signal based on volume and price above VWAP
        return "Sell_Route"  # Route to high-liquidity exchange for selling

    return "Hold"  # No strong routing preference based on current conditions

# Run Smart Order Routing strategy based only on Volume and VWAP, with stop-loss and target
# Run Smart Order Routing strategy based only on Volume and VWAP, with stop-loss and target
def run_smart_order_routing(data, initial_balance, volume_ma, stop_loss_pct, target_pct):
    balance = initial_balance
    position = None  # "Buy" or "Sell" position
    trade_price = None  # Entry price for the current trade
    stop_loss_price = None  # Stop loss price
    target_price = None  # Target price
    position_size = 1  # Assume 1 unit per trade, adjust as needed

    print(f"Starting Smart Order Routing with Initial Balance: {balance}\n")

    for index, row in data.iterrows():
        current_price = row['close']
        volume = row['Volume']
        vwap = row['VWAP']

        # Log current market data
        print(f"Minute {index + 1}: Price={current_price:.2f}, VWAP={vwap:.2f}, Volume={volume}")

        # Check if we should enter a routed position
        if position is None:
            routing_decision_result = routing_decision(row, volume_ma)
            if routing_decision_result == "Buy_Route":
                position = "Buy"
                trade_price = current_price
                stop_loss_price = trade_price * (1 - stop_loss_pct / 100)
                target_price = trade_price * (1 + target_pct / 100)
                print(f"Routing Buy Order at {trade_price:.2f} with VWAP Benchmark at {vwap:.2f}. Stop Loss at {stop_loss_price:.2f}, Target at {target_price:.2f}")
            elif routing_decision_result == "Sell_Route":
                position = "Sell"
                trade_price = current_price
                stop_loss_price = trade_price * (1 + stop_loss_pct / 100)  # Reverse logic for short positions
                target_price = trade_price * (1 - target_pct / 100)  # Reverse logic for short positions
                print(f"Routing Sell Order at {trade_price:.2f} with VWAP Benchmark at {vwap:.2f}. Stop Loss at {stop_loss_price:.2f}, Target at {target_price:.2f}")

        # Monitor routing positions and check for stop-loss or target
        if position == "Buy":
            if current_price <= stop_loss_price:
                print(f"Stop Loss hit for Buy: Current Price={current_price:.2f}, Stop Loss={stop_loss_price:.2f}")
                balance -= position_size * (trade_price - current_price)  # Loss taken based on position size
                position = None
            elif current_price >= target_price:
                print(f"Target hit for Buy: Current Price={current_price:.2f}, Target={target_price:.2f}")
                balance += position_size * (current_price - trade_price)  # Profit taken based on position size
                position = None

        if position == "Sell":
            if current_price >= stop_loss_price:
                print(f"Stop Loss hit for Sell: Current Price={current_price:.2f}, Stop Loss={stop_loss_price:.2f}")
                balance += position_size * (trade_price - current_price)  # Loss taken for short position
                position = None
            elif current_price <= target_price:
                print(f"Target hit for Sell: Current Price={current_price:.2f}, Target={target_price:.2f}")
                balance -= position_size * (trade_price - current_price)  # Profit taken for short position
                position = None

        # Risk management: stop routing if balance falls significantly
        if balance <= initial_balance * 0.7:
            print(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    print(f"Final Balance: {balance:.2f}")

# Correct the file path using os.path
file_path = os.path.join(os.getcwd(), './Smart_Routing/NSE_NIFTY, 1 Intraday.csv')

# Define your parameters here
params = {
    'initial_balance': 10000,  # Starting balance for trading
    'volume_ma': 1000000,  # Volume moving average threshold
    'stop_loss_pct': 0.1,  # Stop loss percentage (e.g., 0.1% stop loss)
    'target_pct': 0.1  # Target percentage (e.g., 0.1% target)
}

# Run strategy with data
try:
    data = load_market_data(file_path)
    run_smart_order_routing(
        data,
        initial_balance=params['initial_balance'],
        volume_ma=params['volume_ma'],
        stop_loss_pct=params['stop_loss_pct'],
        target_pct=params['target_pct']
    )
except FileNotFoundError:
    print(f"File not found: {file_path}")
