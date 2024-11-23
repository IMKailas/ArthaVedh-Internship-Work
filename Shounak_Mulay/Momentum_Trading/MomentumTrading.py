import random
import time

# Function to simulate fetching real-time data from APIs (mock data for demonstration)
def get_market_data():
    market_data = {
        "volume": random.randint(500, 2000),      # Simulate volume
        "macd": random.uniform(-1, 1),            # Random MACD value between -1 and 1
        "signal_line": random.uniform(-1, 1),     # Simulated signal line for MACD
        "rsi": random.uniform(0, 100)             # Random RSI value between 0 and 100
    }
    return market_data

def momentum_decision(market_data):
    volume = market_data["volume"]
    macd = market_data["macd"]
    signal_line = market_data["signal_line"]
    rsi = market_data["rsi"]

    # Define threshold conditions
    min_volume = 800  # Minimum volume threshold
    rsi_oversold = 30  # RSI below 30 indicates oversold condition

    print(f"Volume: {volume}, MACD: {macd:.2f}, Signal Line: {signal_line:.2f}, RSI: {rsi:.2f}")

    # Make trading decision based on parameters
    if volume >= min_volume and macd > signal_line and rsi < rsi_oversold:
        return "Buy"  # Bullish momentum in an oversold condition

    return "Hold"  # No strong indication to buy

def simulate_price_change(entry_price, rsi, macd):
    # Define price change based on indicators
    price_change = random.uniform(0.1, 2)  # Base price change
    if rsi < 30 and macd > 0:  # Bullish conditions
        price_change *= 1.5  # Amplify positive change
    return round(entry_price + price_change, 2)

def run_momentum_strategy(initial_balance, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None     # Only "Buy" position is allowed
    trade_price = None  # Entry price for the current trade
    stop_loss = None    # Stop loss price
    target_profit = None  # Target profit price
    
    # Initialize the price to a random value
    trade_price = round(random.uniform(100, 200), 2)

    while True:
        market_data = get_market_data()  # Get the market data

        # Use the simulated RSI and MACD from market data
        rsi = market_data["rsi"]
        macd = market_data["macd"]
        volume = market_data["volume"]

        # If there is no open position, decide whether to enter a new position
        if position is None:
            decision = momentum_decision(market_data)  # Make momentum decision based on market data

            if decision == "Buy":
                position = "Buy"
                stop_loss = trade_price * (1 - stop_loss_pct / 100)  # Calculate stop loss for Buy position
                target_profit = trade_price * (1 + target_profit_pct / 100)  # Calculate target profit for Buy position
                print(f"Entering Buy position at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target at {target_profit:.2f}")

        # If in a position, simulate price change and check stop loss/target profit
        if position == "Buy":
            current_price = simulate_price_change(trade_price, rsi, macd)
            
            # Check for stop loss or target profit conditions
            if current_price <= stop_loss:
                print(f"Stop Loss hit on Buy! Exiting trade at {current_price:.2f}")
                balance -= (trade_price - current_price)  # Deduct loss
                position = None  # Exit position
            elif current_price >= target_profit:
                print(f"Target Profit reached on Buy! Exiting trade at {current_price:.2f}")
                balance += (current_price - trade_price)  # Add profit
                position = None  # Exit position

            print(f"Current Price: {current_price:.2f}, Balance: {balance:.2f}")

            # Break if balance drops significantly (optional risk management)
            if balance <= initial_balance * 0.7:  # Example: 30% loss of initial balance stops trading
                print(f"Balance dropped below 70% of initial value. Stopping strategy.")
                break
        
        time.sleep(1)  # Simulate a time delay between market data updates

# Run the momentum trading strategy
initial_balance = 10000  # Starting trading balance
stop_loss_pct = 0.5      # 0.5% stop loss
target_profit_pct = 1  # 1% target profit

run_momentum_strategy(initial_balance, stop_loss_pct, target_profit_pct)
