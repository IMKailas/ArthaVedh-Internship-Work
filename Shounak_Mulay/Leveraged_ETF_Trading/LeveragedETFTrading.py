import random
import time

# Function to simulate fetching real-time data for a leveraged ETF
def get_leveraged_etf_data():
    etf_data = {
        "price": round(random.uniform(100, 200), 2),          # Simulated price
        "volatility": round(random.uniform(1, 3), 2),         # Simulate high volatility
        "market_trend": random.choice(["up", "down"]),        # Simulate market trend
    }
    return etf_data

# Function to make trading decisions based on volatility and market trend
def leveraged_etf_decision(etf_data):
    price = etf_data["price"]
    volatility = etf_data["volatility"]
    market_trend = etf_data["market_trend"]

    # Threshold conditions
    high_volatility_threshold = 2.0  # Arbitrary threshold for high volatility

    print(f"Price: {price}, Volatility: {volatility}, Market Trend: {market_trend}")

    # Trading logic based on volatility and market trend
    if volatility >= high_volatility_threshold and market_trend == "up":
        return "Buy"  # Buy leveraged ETF in an uptrend with high volatility
    elif volatility >= high_volatility_threshold and market_trend == "down":
        return "Sell"  # Short-sell or exit in a downtrend with high volatility

    return "Hold"  # No strong trend to act upon

# Simulate price changes based on volatility and trend
def simulate_etf_price_change(entry_price, volatility, trend):
    price_change = round(random.uniform(0.1, 2) * volatility, 2)
    if trend == "up":
        price_change *= 1.5  # Increase in an uptrend
    elif trend == "down":
        price_change *= -1.2  # Decrease in a downtrend
    return round(entry_price + price_change, 2)

# Run the leveraged ETF trading strategy
def run_leveraged_etf_strategy(initial_balance, leverage, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None       # Track open position ("Buy" or "Sell")
    trade_price = None    # Entry price for the current trade
    stop_loss = None      # Stop loss price
    target_profit = None  # Target profit price
    
    # Initialize trade price to a random value
    trade_price = round(random.uniform(100, 200), 2)

    while True:
        etf_data = get_leveraged_etf_data()  # Get market data for leveraged ETF
        volatility = etf_data["volatility"]
        trend = etf_data["market_trend"]

        # Make trading decision if no open position
        if position is None:
            decision = leveraged_etf_decision(etf_data)

            if decision == "Buy":
                position = "Buy"
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy position at {trade_price} with Stop Loss at {stop_loss} and Target at {target_profit}")

            elif decision == "Sell":
                position = "Sell"
                stop_loss = trade_price * (1 + stop_loss_pct / 100)
                target_profit = trade_price * (1 - target_profit_pct / 100)
                print(f"Entering Sell position at {trade_price} with Stop Loss at {stop_loss} and Target at {target_profit}")

        # If in a position, simulate price change and check stop loss/target profit
        if position:
            current_price = simulate_etf_price_change(trade_price, volatility, trend)

            # Adjust for leveraged impact on balance
            leveraged_gain_loss = (current_price - trade_price) * leverage

            # Check if current price hits stop loss or target profit
            if position == "Buy" and current_price <= stop_loss:
                print(f"Stop Loss hit on Buy! Exiting trade at {current_price}")
                balance -= leveraged_gain_loss
                position = None
            elif position == "Buy" and current_price >= target_profit:
                print(f"Target Profit reached on Buy! Exiting trade at {current_price}")
                balance += leveraged_gain_loss
                position = None
            elif position == "Sell" and current_price >= stop_loss:
                print(f"Stop Loss hit on Sell! Exiting trade at {current_price}")
                balance -= leveraged_gain_loss
                position = None
            elif position == "Sell" and current_price <= target_profit:
                print(f"Target Profit reached on Sell! Exiting trade at {current_price}")
                balance += leveraged_gain_loss
                position = None

            print(f"Current Price: {current_price}, Balance: {balance}")

            # Optional: stop strategy if balance drops significantly
            if balance <= initial_balance * 0.7:
                print("Balance dropped below 70% of initial value. Stopping strategy.")
                break
        
        time.sleep(1)  # Simulate time delay for each iteration

# Run the leveraged ETF strategy
initial_balance = 10000  # Starting balance
leverage = 3             # 3x leveraged ETF
stop_loss_pct = 5        # 5% stop loss
target_profit_pct = 10   # 10% target profit

run_leveraged_etf_strategy(initial_balance, leverage, stop_loss_pct, target_profit_pct)
