import random
import time

# Function to simulate fetching real-time data from APIs (mock data for demonstration)
def get_market_data():
    market_data = {
        "price": round(random.uniform(100, 200), 2),  # Simulate current price
        "volume": random.randint(500, 2000)          # Simulate volume
    }
    return market_data

def micro_futures_decision(market_data, position):
    volume = market_data["volume"]
    
    # Define threshold conditions
    min_volume = 800  # Minimum volume threshold

    print(f"Price: {market_data['price']:.2f}, Volume: {volume}")

    # Make trading decision based on parameters
    if position is None and volume >= min_volume:
        return random.choice(["Buy", "Sell"])  # Decide to Buy or Sell when volume is high

    return "Hold"  # No strong indication to trade

def simulate_price_change(entry_price, volume):
    # Define price change based on volume
    price_change = random.uniform(0.1, 2)  # Base price change
    if volume >= 800:  # High volume conditions
        price_change *= 1.5  # Amplify change
    else:
        price_change *= 0.8  # Reduce change

    # Randomly decide direction of price change
    return round(entry_price + price_change * random.choice([-1, 1]), 2)

def run_micro_futures_strategy(initial_balance, leverage, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None     # Can be "Buy" or "Sell"
    trade_price = None  # Entry price for the current trade
    stop_loss = None    # Stop loss price
    target_profit = None  # Target profit price

    while True:
        market_data = get_market_data()  # Get the market data

        # Use the simulated price and volume from market data
        price = market_data["price"]
        volume = market_data["volume"]

        # If there is no open position, decide whether to enter a new position
        if position is None:
            decision = micro_futures_decision(market_data, position)  # Make trading decision based on market data

            if decision == "Buy":
                position = "Buy"
                trade_price = price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)  # Calculate stop loss for Buy position
                target_profit = trade_price * (1 + target_profit_pct / 100)  # Calculate target profit for Buy position
                print(f"Entering Buy position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")

            elif decision == "Sell":
                position = "Sell"
                trade_price = price
                stop_loss = trade_price * (1 + stop_loss_pct / 100)  # Calculate stop loss for Sell position
                target_profit = trade_price * (1 - target_profit_pct / 100)  # Calculate target profit for Sell position
                print(f"Entering Sell position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")

        # If in a position, simulate price change and check stop loss/target profit
        if position:
            current_price = simulate_price_change(trade_price, volume)

            # Check for stop loss or target profit conditions
            if position == "Buy":
                if current_price <= stop_loss:
                    print(f"Stop Loss hit on Buy! Exiting trade at {current_price:.2f}")
                    balance -= (trade_price - current_price) * leverage  # Deduct leveraged loss
                    position = None  # Exit position
                elif current_price >= target_profit:
                    print(f"Target Profit reached on Buy! Exiting trade at {current_price:.2f}")
                    balance += (current_price - trade_price) * leverage  # Add leveraged profit
                    position = None  # Exit position

            elif position == "Sell":
                if current_price >= stop_loss:
                    print(f"Stop Loss hit on Sell! Exiting trade at {current_price:.2f}")
                    balance -= (current_price - trade_price) * leverage  # Deduct leveraged loss
                    position = None  # Exit position
                elif current_price <= target_profit:
                    print(f"Target Profit reached on Sell! Exiting trade at {current_price:.2f}")
                    balance += (trade_price - current_price) * leverage  # Add leveraged profit
                    position = None  # Exit position

            print(f"Current Price: {current_price:.2f}, Balance: {balance:.2f}")

            # Break if balance drops significantly (optional risk management)
            if balance <= initial_balance * 0.7:  # Example: 30% loss of initial balance stops trading
                print(f"Balance dropped below 70% of initial value. Stopping strategy.")
                break

        time.sleep(1)  # Simulate a time delay between market data updates

# Run the micro futures trading strategy
initial_balance = 10000  # Starting trading balance
leverage = 10            # 10x leverage for micro futures
stop_loss_pct = 0.5      # 0.5% stop loss
target_profit_pct = 1    # 1% target profit

run_micro_futures_strategy(initial_balance, leverage, stop_loss_pct, target_profit_pct)
