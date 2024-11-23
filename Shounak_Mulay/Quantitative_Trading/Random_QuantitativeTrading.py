import random
import time

# Function to simulate fetching real-time data (mock data)
def get_market_data():
    market_data = {
        "price": random.uniform(100, 200),
        "macd": random.uniform(-1, 1),
        "signal": random.uniform(-1, 1),
        "rsi": random.uniform(0, 100),
        "volume": random.uniform(1000, 5000),
        "volume_ma": random.uniform(1000, 5000),
        "upper_band": random.uniform(150, 200),
        "lower_band": random.uniform(100, 150),
        "vwap": random.uniform(100, 200),
        "k_percent": random.uniform(0, 100),
        "d_percent": random.uniform(0, 100)
    }
    return market_data

# Function to decide whether to place a trade based on quantitative indicators
def quantitative_decision(market_data):
    macd = market_data["macd"]
    signal = market_data["signal"]
    rsi = market_data["rsi"]
    price = market_data["price"]
    volume = market_data["volume"]
    volume_ma = market_data["volume_ma"]
    upper_band = market_data["upper_band"]
    lower_band = market_data["lower_band"]
    vwap = market_data["vwap"]
    k_percent = market_data["k_percent"]
    d_percent = market_data["d_percent"]

    # Define thresholds for technical indicators
    rsi_overbought = 70
    rsi_oversold = 30

    print(f"Price: {price:.2f}, MACD: {macd:.2f}, Signal: {signal:.2f}, RSI: {rsi:.2f}, VWAP: {vwap:.2f}")

    # Trading decision logic based on available indicators
    if rsi < rsi_oversold and macd > signal and price < lower_band and volume > volume_ma:
        return "Buy"  # Strong Buy signal based on oversold condition, MACD, Bollinger Bands, and volume confirmation
    elif rsi > rsi_overbought and macd < signal and price > upper_band and volume < volume_ma:
        return "Sell"  # Strong Sell signal based on overbought condition, MACD, Bollinger Bands, and volume confirmation

    return "Hold"  # No strong indication to trade

# Simulate price changes based on current indicators
def simulate_price_change(entry_price, macd, rsi):
    price_change = random.uniform(0.1, 2)
    if rsi < 30 and macd > 0:
        price_change *= 1.5  # Amplify positive change
    elif rsi > 70 and macd < 0:
        price_change *= -1.5  # Amplify negative change
    return round(entry_price + price_change, 2)

# Run the quantitative trading strategy
def run_quantitative_strategy(initial_balance, stop_loss_pct, target_profit_pct):
    balance = initial_balance
    position = None      # Track open position ("Buy" or "Sell")
    trade_price = None   # Entry price for the current trade
    stop_loss = None     # Stop loss price
    target_profit = None # Target profit price

    trade_price = round(random.uniform(100, 200), 2)

    while True:
        market_data = get_market_data()
        macd = market_data["macd"]
        rsi = market_data["rsi"]

        if position is None:
            decision = quantitative_decision(market_data)

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

        if position in ["Buy", "Sell"]:
            current_price = simulate_price_change(trade_price, macd, rsi)

            if position == "Buy":
                if current_price <= stop_loss:
                    print(f"Stop Loss hit on Buy! Exiting trade at {current_price:.2f}")
                    balance -= (trade_price - current_price)
                    position = None
                elif current_price >= target_profit:
                    print(f"Target Profit reached on Buy! Exiting trade at {current_price:.2f}")
                    balance += (current_price - trade_price)
                    position = None

            elif position == "Sell":
                if current_price >= stop_loss:
                    print(f"Stop Loss hit on Sell! Exiting trade at {current_price:.2f}")
                    balance -= (current_price - trade_price)
                    position = None
                elif current_price <= target_profit:
                    print(f"Target Profit reached on Sell! Exiting trade at {current_price:.2f}")
                    balance += (trade_price - current_price)
                    position = None

            print(f"Current Price: {current_price:.2f}, Balance: {balance:.2f}")

            if balance <= initial_balance * 0.7:
                print("Balance dropped below 70% of initial value. Stopping strategy.")
                break
        
        time.sleep(1)

# Run the quantitative trading strategy
initial_balance = 10000
stop_loss_pct = 0.5
target_profit_pct = 1

run_quantitative_strategy(initial_balance, stop_loss_pct, target_profit_pct)
