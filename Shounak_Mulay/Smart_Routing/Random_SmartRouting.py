import random
import time

# Function to simulate fetching real-time data (mock data)
def get_market_data():
    market_data = {
        "volume": random.randint(500, 2000),  # Simulate volume
        "order_flow": random.randint(-100, 100)  # Random order flow (buy/sell imbalance)
    }
    return market_data

# Function to decide whether to place an order based on smart routing
def smart_routing_decision(market_data):
    volume = market_data["volume"]
    order_flow = market_data["order_flow"]

    # Define threshold conditions
    high_volume_threshold = 1200  # High volume threshold
    buy_order_flow_threshold = 50  # Positive order flow threshold for buying
    sell_order_flow_threshold = -50  # Negative order flow threshold for selling

    print(f"Volume: {volume}, Order Flow: {order_flow}")

    # Make trading decision based on volume and order flow
    if volume >= high_volume_threshold:
        if order_flow >= buy_order_flow_threshold:
            return "Buy"  # Indicates bullish order flow in high volume conditions
        elif order_flow <= sell_order_flow_threshold:
            return "Sell"  # Indicates bearish order flow in high volume conditions

    return "Hold"  # No strong indication to trade

# Simulate price changes based on order flow direction
def simulate_price_change(entry_price, order_flow):
    # Price moves up with positive order flow, down with negative order flow
    price_change = random.uniform(0.1, 2)
    if order_flow > 0:
        price_change *= 1.1  # Amplify change for positive order flow
    elif order_flow < 0:
        price_change *= -1.1  # Amplify change for negative order flow
    return round(entry_price + price_change, 2)

# Run the smart routing trading strategy
def run_smart_routing_strategy(initial_balance, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None      # Track open position (None, "Buy", "Sell")
    trade_price = None   # Entry price for the current trade
    stop_loss = None     # Stop loss price
    target_profit = None # Target profit price

    # Initialize the price to a random value
    trade_price = round(random.uniform(100, 200), 2)

    while True:
        market_data = get_market_data()  # Get the market data
        order_flow = market_data["order_flow"]

        # Decide whether to place an order based on market conditions
        if position is None:
            decision = smart_routing_decision(market_data)

            if decision == "Buy":
                position = "Buy"
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")

            elif decision == "Sell":
                position = "Sell"
                stop_loss = trade_price * (1 + stop_loss_pct / 100)
                target_profit = trade_price * (1 - target_profit_pct / 100)
                print(f"Entering Sell position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")

        # If in a position, simulate price change and check stop loss/target profit
        if position in ["Buy", "Sell"]:
            current_price = simulate_price_change(trade_price, order_flow)

            # Check for stop loss or target profit conditions
            if position == "Buy":
                if current_price <= stop_loss:
                    print(f"Stop Loss hit on Buy! Exiting trade at {current_price:.2f}")
                    balance -= (trade_price - current_price)  # Deduct loss
                    position = None
                elif current_price >= target_profit:
                    print(f"Target Profit reached on Buy! Exiting trade at {current_price:.2f}")
                    balance += (current_price - trade_price)  # Add profit
                    position = None

            elif position == "Sell":
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
            if balance <= initial_balance * 0.7:
                print("Balance dropped below 70% of initial value. Stopping strategy.")
                break
        
        time.sleep(1)  # Simulate a time delay between market data updates

# Run the smart routing strategy
initial_balance = 10000  # Starting trading balance
stop_loss_pct = 0.5      # 0.5% stop loss
target_profit_pct = 1    # 1% target profit

run_smart_routing_strategy(initial_balance, stop_loss_pct, target_profit_pct)
