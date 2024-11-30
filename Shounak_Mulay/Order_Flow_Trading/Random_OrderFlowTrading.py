import random
import time

# Function to simulate fetching real-time order flow data (mock data)
def get_market_data():
    market_data = {
        "price": random.uniform(100, 200),
        "order_flow": random.uniform(-1000, 1000),  # Positive for buy pressure, negative for sell pressure
        "volume": random.uniform(1000, 5000),
        "volume_ma": random.uniform(1000, 5000)    # Moving average of volume
    }
    return market_data

# Function to decide whether to place a trade based on order flow and volume
def order_flow_decision(market_data):
    order_flow = market_data["order_flow"]
    volume = market_data["volume"]
    volume_ma = market_data["volume_ma"]
    price = market_data["price"]

    print(f"Price: {price:.2f}, Order Flow: {order_flow:.2f}, Volume: {volume:.2f}, Volume MA: {volume_ma:.2f}")

    # Decision logic based on order flow and volume
    if order_flow > 500 and volume > volume_ma:  # Strong buy pressure and high volume
        return "Buy"
    elif order_flow < -500 and volume > volume_ma:  # Strong sell pressure and high volume
        return "Sell"
    return "Hold"  # No strong signal to trade

# Simulate price changes based on order flow
def simulate_price_change(entry_price, order_flow):
    price_change = random.uniform(0.1, 2)
    if order_flow > 500:
        price_change *= 1.5  # Amplify positive change
    elif order_flow < -500:
        price_change *= -1.5  # Amplify negative change
    return round(entry_price + price_change, 2)

# Run the order flow trading strategy
def run_order_flow_strategy(initial_balance, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None      # Track open position ("Buy" or "Sell")
    trade_price = None   # Entry price for the current trade
    stop_loss = None     # Stop loss price
    target_profit = None # Target profit price

    while True:
        market_data = get_market_data()
        order_flow = market_data["order_flow"]

        if position is None:  # No position open
            decision = order_flow_decision(market_data)

            if decision == "Buy":
                position = "Buy"
                trade_price = market_data["price"]
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")

        elif position == "Buy":  # Only sell if a buy position is open
            current_price = simulate_price_change(trade_price, order_flow)

            if current_price <= stop_loss:
                print(f"Stop Loss hit on Buy! Exiting trade at {current_price:.2f}")
                balance -= (trade_price - current_price)
                position = None
            elif current_price >= target_profit:
                print(f"Target Profit reached on Buy! Exiting trade at {current_price:.2f}")
                balance += (current_price - trade_price)
                position = None

            print(f"Current Price: {current_price:.2f}, Balance: {balance:.2f}")

        if balance <= initial_balance * 0.7:
            print("Balance dropped below 70% of initial value. Stopping strategy.")
            break

        time.sleep(1)

# Run the order flow trading strategy
initial_balance = 10000
stop_loss_pct = 0.5
target_profit_pct = 1

run_order_flow_strategy(initial_balance, stop_loss_pct, target_profit_pct)
