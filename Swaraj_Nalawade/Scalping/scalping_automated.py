import random
import time

# Sample function to simulate fetching real-time data from APIs (mock data for demonstration)
def get_market_data():
    # Mock data: Replace with API calls to fetch real-time data (bid, ask, volume, order flow)
    market_data = {
        "bid_price": round(random.uniform(100, 102), 2),  # Simulate bid price between 100 and 102
        "ask_price": round(random.uniform(101, 102), 2),  # Simulate ask price between 101 and 102
        "volume": random.randint(500, 2000),              # Simulate volume between 500 and 2000
        "buy_orders": random.randint(50, 200),            # Simulate buy orders
        "sell_orders": random.randint(50, 200),           # Simulate sell orders
    }
    return market_data

# Function to calculate spread, order flow ratio, and make trading decisions
def scalping_decision(market_data):
    bid_price = market_data["bid_price"]
    ask_price = market_data["ask_price"]
    volume = market_data["volume"]
    buy_orders = market_data["buy_orders"]
    sell_orders = market_data["sell_orders"]

    # Calculate Bid-Ask Spread
    spread = ask_price - bid_price

    # Calculate Order Flow (buy/sell ratio)
    order_flow_ratio = buy_orders / sell_orders if sell_orders > 0 else float('inf')

    # Define threshold conditions (these can be tuned based on market behavior)
    max_spread = 0.1  # Adjusted to allow for a higher spread tolerance
    min_volume = 800  # Lowered volume threshold
    min_order_flow_ratio = 1.1  # Adjusted order flow ratio for more flexibility

    print(f"Bid: {bid_price}, Ask: {ask_price}, Spread: {spread:.2f}, Volume: {volume}, Order Flow Ratio: {order_flow_ratio:.2f}")

    # Make trading decision based on parameters
    if spread <= max_spread and volume >= min_volume:
        if order_flow_ratio >= min_order_flow_ratio:
            return "Buy"  # More buy orders and tight spread, suggest a buy
        elif order_flow_ratio <= 1 / min_order_flow_ratio:
            return "Sell"  # More sell orders, suggest a sell
    return "Hold"  # No strong indication to buy or sell

# Function to simulate the price changes after a trade is made
def simulate_price_change(entry_price, direction):
    # Random price fluctuations for simulation
    if direction == "Buy":
        return round(entry_price + random.uniform(-0.5, 1), 2)  # Simulate price going up or down
    elif direction == "Sell":
        return round(entry_price - random.uniform(-0.5, 1), 2)  # Simulate price going down or up
    return entry_price

# Main function to run the scalping strategy in a loop
def run_scalping_strategy(initial_balance, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None     # "Buy" or "Sell" position
    trade_price = None  # Entry price for the current trade
    stop_loss = None    # Stop loss price
    target_profit = None  # Target profit price
    
    while True:
        market_data = get_market_data()  # Get the market data

        # If there is no open position, decide whether to enter a new position
        if position is None:
            decision = scalping_decision(market_data)  # Make scalping decision

            if decision == "Buy":
                position = "Buy"
                trade_price = market_data["ask_price"]  # Enter at ask price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)  # Calculate stop loss for Buy position
                target_profit = trade_price * (1 + target_profit_pct / 100)  # Calculate target profit for Buy position
                print(f"Entering Buy position at {trade_price} with Stop Loss at {stop_loss} and Target at {target_profit}")
            elif decision == "Sell":
                position = "Sell"
                trade_price = market_data["bid_price"]  # Enter at bid price
                stop_loss = trade_price * (1 + stop_loss_pct / 100)  # Calculate stop loss for Sell position
                target_profit = trade_price * (1 - target_profit_pct / 100)  # Calculate target profit for Sell position
                print(f"Entering Sell position at {trade_price} with Stop Loss at {stop_loss} and Target at {target_profit}")

        # If in a position, simulate price change and check stop loss/target profit
        if position is not None:
            current_price = simulate_price_change(trade_price, position)
            
            # Check for stop loss or target profit conditions
            if position == "Buy":
                if current_price <= stop_loss:
                    print(f"Stop Loss hit on Buy! Exiting trade at {current_price}")
                    balance -= (trade_price - current_price)  # Deduct loss
                    position = None  # Exit position
                elif current_price >= target_profit:
                    print(f"Target Profit reached on Buy! Exiting trade at {current_price}")
                    balance += (current_price - trade_price)  # Add profit
                    position = None  # Exit position
            elif position == "Sell":
                if current_price >= stop_loss:
                    print(f"Stop Loss hit on Sell! Exiting trade at {current_price}")
                    balance -= (current_price - trade_price)  # Deduct loss
                    position = None  # Exit position
                elif current_price <= target_profit:
                    print(f"Target Profit reached on Sell! Exiting trade at {current_price}")
                    balance += (trade_price - current_price)  # Add profit
                    position = None  # Exit position

            print(f"Current Price: {current_price}, Balance: {balance:.2f}")

            # Break if balance drops significantly (optional risk management)
            if balance <= initial_balance * 0.7:  # Example: 30% loss of initial balance stops trading
                print(f"Balance dropped below 70% of initial value. Stopping strategy.")
                break
        
        time.sleep(1)  # Simulate a time delay between market data updates

# Run the strategy with initial balance, stop loss percentage, and target profit percentage
initial_balance = 10000  # Starting trading balance
stop_loss_pct = 0.5      # 0.5% stop loss
target_profit_pct = 0.5  # 0.5% target profit

run_scalping_strategy(initial_balance, stop_loss_pct, target_profit_pct)
