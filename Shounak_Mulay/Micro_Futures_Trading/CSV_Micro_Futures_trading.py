import pandas as pd
import time
import os
# Load data from a CSV file
def load_market_data(csv_file):
    return pd.read_csv(filepath_or_buffer=csv_file)

def micro_futures_decision(row, position, entry_made):
    volume = row["Volume"]
    
    # Define threshold conditions
    min_volume = 800  # Minimum volume threshold

    print(f"Time: {row['time']}, Price: {row['close']:.2f}, Volume: {volume}")

    # Make trading decision based on parameters
    if position is None and not entry_made and volume >= min_volume:
        return "Buy" if row['RSI'] < 30 else "Sell"  # Buy if oversold, Sell if overbought

    return "Hold"  # No strong indication to trade

def run_micro_futures_strategy(csv_file, initial_balance, leverage, stop_loss_pct, target_profit_pct):
    data = load_market_data(csv_file)  # Load market data from CSV
    balance = initial_balance
    position = None     # Can be "Buy" or "Sell"
    trade_price = None  # Entry price for the current trade
    stop_loss = None    # Stop loss price
    target_profit = None  # Target profit price
    entry_made = False

    for _, row in data.iterrows():
        price = row["close"]
        volume = row["Volume"]

        # If there is no open position, decide whether to enter a new position
        if position is None:
            decision = micro_futures_decision(row, position, entry_made)  # Make trading decision based on market data

            if decision == "Buy":
                position = "Buy"
                trade_price = price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)  # Calculate stop loss for Buy position
                target_profit = trade_price * (1 + target_profit_pct / 100)  # Calculate target profit for Buy position
                print(f"Entering Buy position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")
                entry_made = True

            elif decision == "Sell":
                position = "Sell"
                trade_price = price
                stop_loss = trade_price * (1 + stop_loss_pct / 100)  # Calculate stop loss for Sell position
                target_profit = trade_price * (1 - target_profit_pct / 100)  # Calculate target profit for Sell position
                print(f"Entering Sell position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")
                entry_made = True

        # If in a position, check stop loss/target profit
        if position:
            current_price = price

            if position == "Buy":
                if current_price <= stop_loss:
                    print(f"Stop Loss hit on Buy! Exiting trade at {current_price:.2f}")
                    balance -= (trade_price - current_price) * leverage  # Deduct leveraged loss
                    position = None  # Exit position
                    trade_price = None
                    entry_made = False
                elif current_price >= target_profit:
                    print(f"Target Profit reached on Buy! Exiting trade at {current_price:.2f}")
                    balance += (current_price - trade_price) * leverage  # Add leveraged profit
                    position = None  # Exit position
                    trade_price = None
                    entry_made = False

            elif position == "Sell":
                if current_price >= stop_loss:
                    print(f"Stop Loss hit on Sell! Exiting trade at {current_price:.2f}")
                    balance -= (current_price - trade_price) * leverage  # Deduct leveraged loss
                    position = None  # Exit position
                    trade_price = None
                    entry_made = False
                elif current_price <= target_profit:
                    print(f"Target Profit reached on Sell! Exiting trade at {current_price:.2f}")
                    balance += (trade_price - current_price) * leverage  # Add leveraged profit
                    position = None  # Exit position
                    trade_price = None
                    entry_made = False

            print(f"Current Price: {current_price:.2f}, Balance: {balance:.2f}")

            # Break if balance drops significantly (optional risk management)
            if balance <= initial_balance * 0.7:  # Example: 30% loss of initial balance stops trading
                print(f"Balance dropped below 70% of initial value. Stopping strategy.")
                break

        time.sleep(1)  # Simulate a time delay between rows for real-time feel

    if position:
        print(f"Final Position ({position}) at {trade_price:.2f} was not closed. Please manually evaluate remaining exposure.")

# Run the micro futures trading strategy
csv_file = os.path.join(os.getcwd(), './Momentum_Trading/NSE_NIFTY, 1 Intraday.csv')

initial_balance = 10000  # Starting trading balance
leverage = 10            # 10x leverage for micro futures
stop_loss_pct = 0.5      # 0.5% stop loss
target_profit_pct = 1    # 1% target profit

run_micro_futures_strategy(csv_file, initial_balance, leverage, stop_loss_pct, target_profit_pct)


