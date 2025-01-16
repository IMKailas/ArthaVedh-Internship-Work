import pandas as pd
import os
from config_SmartRouting import *  # Import configuration from config.py

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
    return "Hold"  # No strong routing preference based on current conditions

# Run Smart Order Routing strategy based only on Volume and VWAP, with stop-loss and target
def run_smart_order_routing(data, initial_balance, volume_ma, stop_loss_pct, target_pct):
    balance = initial_balance
    position = None  # "Buy" or "Sell" position
    trade_price = None  # Entry price for the current trade
    stop_loss_price = None  # Stop loss price
    target_price = None  # Target price
    position_size = 1  # Assume 1 unit per trade, adjust as needed

    # Summary variables
    trades = []
    total_profit = 0
    total_loss = 0
    successful_trades = 0
    failed_trades = 0

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

        # Monitor routing positions and check for stop-loss or target
        if position == "Buy":
            if current_price <= stop_loss_price:
                print(f"Stop Loss hit for Buy: Current Price={current_price:.2f}, Stop Loss={stop_loss_price:.2f}")
                loss = trade_price - current_price
                balance -= position_size * loss  # Loss taken based on position size
                total_loss += loss
                failed_trades += 1
                trades.append({"Entry Price": trade_price, "Exit Price": current_price, "PnL": -loss, "Reason": "Stop Loss"})
                position = None
            elif current_price >= target_price:
                print(f"Target hit for Buy: Current Price={current_price:.2f}, Target={target_price:.2f}")
                profit = current_price - trade_price
                balance += position_size * profit  # Profit taken based on position size
                total_profit += profit
                successful_trades += 1
                trades.append({"Entry Price": trade_price, "Exit Price": current_price, "PnL": profit, "Reason": "Target Profit"})
                position = None

        # Risk management: stop routing if balance falls significantly
        if balance <= initial_balance * 0.7:
            print(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    # Summary of trades
    print("\n--- Trade Summary ---")
    print(f"Total Trades: {len(trades)}")
    print(f"Successful Trades: {successful_trades}")
    print(f"Failed Trades: {failed_trades}")
    print(f"Total Profit: {total_profit:.2f}")
    print(f"Total Loss: {total_loss:.2f}")
    print(f"Net Profit/Loss: {total_profit - total_loss:.2f}")
    print(f"Final Balance: {balance:.2f} ({((balance - initial_balance) / initial_balance) * 100:.2f}%)")

    # Detailed trade breakdown
    print("\n--- Trade Details ---")
    for i, trade in enumerate(trades, 1):
        print(f"Trade {i}: Entry Price={trade['Entry Price']:.2f}, Exit Price={trade['Exit Price']:.2f}, "
              f"PnL={trade['PnL']:.2f}, Reason={trade['Reason']}")

# Correct the file path using os.path from config
file_path = os.path.join(os.getcwd(), file_path)

# Run strategy with data
try:
    data = load_market_data(file_path)
    run_smart_order_routing(
        data,
        initial_balance=initial_balance,
        volume_ma=volume_ma,
        stop_loss_pct=stop_loss_pct,
        target_pct=target_pct
    )
except FileNotFoundError:
    print(f"File not found: {file_path}")
