import pandas as pd
import os
import random
import config_LeveragedETF
from datetime import datetime

# Function to create log directory if it doesn't exist
def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Leveraged_ETF_Trading/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

# Log trade details to file
def log_trade(message, log_filename):
    with open(log_filename, 'a') as f:
        f.write(f"{message}\n")
    print(message)

# Load CSV data
def load_etf_data(file_path):
    return pd.read_csv(file_path)

# Calculate volatility as the difference between high and low prices
def calculate_volatility(row):
    return row["high"] - row["low"]

# Determine the market trend based on close price and VWAP
def calculate_market_trend(row):
    return "up" if row["close"] > row["VWAP"] else "down"

# Decision-making for leveraged ETF trading
def leveraged_etf_decision(row):
    volatility = calculate_volatility(row)
    market_trend = calculate_market_trend(row)
    high_volatility_threshold = 1.0  # Adjust this value for sensitivity

    # Debugging output
    print(f"Volatility: {volatility}, Trend: {market_trend}, Close: {row['close']}, VWAP: {row['VWAP']}")

    # Buy condition: High volatility and an upward trend
    if volatility >= high_volatility_threshold and market_trend == "up":
        return "Buy"
    return "Hold"

# Simulate price changes based on market conditions
def simulate_etf_price_change(entry_price, volatility, trend):
    price_change = round(random.uniform(0.1, 2) * volatility, 2)
    price_change *= 1.1 if trend == "up" else -1.1
    return round(entry_price + price_change, 2)

# Run the trading strategy
def run_leveraged_etf_strategy(etf_data, initial_balance, leverage, stop_loss_pct, target_profit_pct):
    # Create log file
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"leveraged_etf_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trades = []

    log_trade(f"===========================================", log_filename)
    log_trade(f"  Leveraged ETF Trading Strategy  ", log_filename)
    log_trade(f"===========================================", log_filename)
    log_trade(f"Initial Balance: {balance:.2f}", log_filename)
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%", log_filename)
    log_trade(f"Target Profit Percentage: {target_profit_pct}%", log_filename)

    for _, row in etf_data.iterrows():
        price = row["close"]
        volatility = calculate_volatility(row)
        trend = calculate_market_trend(row)

        # If no active position, decide whether to enter one
        if position is None:
            decision = leveraged_etf_decision(row)
            if decision == "Buy":
                position = "Buy"
                trade_price = price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                
                log_trade(f"Entering Buy position at {trade_price} with Stop Loss at {stop_loss} and Target at {target_profit}", log_filename)

        # Manage an open Buy position
        if position == "Buy":
            current_price = simulate_etf_price_change(trade_price, volatility, trend)
            leveraged_gain_loss = (current_price - trade_price) * leverage

            # Check for stop loss or target profit conditions
            if current_price <= stop_loss:
                log_trade(f"Stop Loss hit! Exiting Buy position at {current_price}", log_filename)
                balance -= leveraged_gain_loss
                trades.append({
                    'entry_price': trade_price,
                    'exit_price': current_price,
                    'status': "Stop Loss",
                    'profit': -leveraged_gain_loss
                })
                position = None
            elif current_price >= target_profit:
                log_trade(f"Target Profit reached! Exiting Buy position at {current_price}", log_filename)
                balance += leveraged_gain_loss
                trades.append({
                    'entry_price': trade_price,
                    'exit_price': current_price,
                    'status': "Target Profit",
                    'profit': leveraged_gain_loss
                })
                position = None

            # Display status
            log_trade(f"Current Price: {current_price}, Balance: {balance}", log_filename)

            # Stop trading if balance drops below a critical threshold
            if balance <= initial_balance * 0.7:
                log_trade("Balance dropped below 70% of initial value. Stopping strategy.", log_filename)
                break

    # Trading Summary
    log_trade("\n===========================================", log_filename)
    log_trade(f"  Trading Summary", log_filename)
    log_trade(f"===========================================", log_filename)
    log_trade(f"Initial Balance: {initial_balance:.2f}", log_filename)
    log_trade(f"Final Balance: {balance:.2f}", log_filename)
    log_trade(f"Total Profit/Loss: {balance - initial_balance:.2f}", log_filename)
    log_trade(f"Total Trades Executed: {len(trades)}", log_filename)

    if len(trades) > 0:
        profit_trades = [trade for trade in trades if trade['profit'] > 0]
        loss_trades = [trade for trade in trades if trade['profit'] < 0]

        log_trade(f"Profitable Trades: {len(profit_trades)}", log_filename)
        log_trade(f"Loss-making Trades: {len(loss_trades)}", log_filename)
        if len(profit_trades) > 0:
            log_trade(f"Average Profit per winning trade: {sum([trade['profit'] for trade in profit_trades]) / len(profit_trades):.2f}", log_filename)
        if len(loss_trades) > 0:
            log_trade(f"Average Loss per losing trade: {sum([trade['profit'] for trade in loss_trades]) / len(loss_trades):.2f}", log_filename)

        # Calculate win rate
        win_rate = len(profit_trades) / len(trades) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%", log_filename)

# Main execution
file_path = os.path.join(os.getcwd(), './Leveraged_ETF_Trading/NSE_NIFTY, 1 Intraday.csv')
etf_data = load_etf_data(file_path)

initial_balance = config_LeveragedETF.initial_balance
leverage = config_LeveragedETF.leverage
stop_loss_pct = config_LeveragedETF.stop_loss_pct
target_profit_pct = config_LeveragedETF.target_profit_pct

run_leveraged_etf_strategy(etf_data, initial_balance, leverage, stop_loss_pct, target_profit_pct)
