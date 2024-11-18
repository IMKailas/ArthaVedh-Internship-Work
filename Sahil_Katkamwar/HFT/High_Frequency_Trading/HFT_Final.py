import random
import time
from collections import deque

# Simulated function to get market prices with random market shocks and trend
def get_market_prices(symbol, trend=0):
    base_price = random.uniform(100, 200)
    shock = random.uniform(-25, 25)  # Wider shock range for more volatility
    price_change = trend + shock  # Simulated trend plus shock
    bid_price = round(base_price + price_change, 2)
    ask_price = round(bid_price + random.uniform(0.01, 5), 2)
    return bid_price, ask_price

# Simulated function to place an order with slippage and transaction costs
def place_order(order_type, symbol, price, shares_count):
    transaction_cost = 0.02 * price * shares_count  # Transaction cost to 2%
    slippage = random.uniform(-2.0, 2.0)  # Increased slippage range
    final_price = price + slippage
    print(f"Placed {order_type} order for {shares_count} shares of {symbol} at {final_price:.2f} (Slippage: {slippage:.2f}) | Transaction cost: {transaction_cost:.2f}")
    return final_price, transaction_cost  # Return price and transaction cost for profit/loss calculation

# Function to calculate moving average
def moving_average(prices, period=5):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

# Function for mean reversion strategy
def mean_reversion_strategy(prices, threshold=5.0):  # Increased threshold for fewer trades
    if len(prices) < 5:
        return None  # Not enough data to calculate mean

    mean_price = sum(prices) / len(prices)
    current_price = prices[-1]
    deviation = current_price - mean_price

    if deviation > threshold:  # Only sell if significantly above mean
        return 'SELL'
    elif deviation < -threshold:  # Only buy if significantly below mean
        return 'BUY'
    return None  # No action

# Exit strategy with additional logic to sell all held shares
def exit_strategy(current_capital, shares_held, bid_price, initial_capital, max_profit=3000, max_loss=-3000):  # Adjusted limits
    total_value = current_capital + (shares_held * bid_price)
    profit_loss = total_value - initial_capital

    if profit_loss >= max_profit:
        print(f"Profit target reached: {profit_loss:.2f}. Exiting all positions.")
        return True
    if profit_loss <= max_loss:
        print(f"Loss limit reached: {profit_loss:.2f}. Exiting all positions.")
        return True

    return False

# Market maker function with realistic modifications
def market_maker(symbol, desired_spread):
    price_history = deque(maxlen=50)  # Store last 50 prices for mean reversion
    prices = []  # Store historical prices for technical indicators

    initial_capital = 100000  # Starting capital
    current_capital = initial_capital
    shares_held = 0  # Track shares held

    # Simulated market trend: could be 0 (neutral), positive (uptrend), or negative (downtrend)
    market_trend = random.choice([0, 0.05, -0.05])

    start_time = time.time()

    while True:
        bid_price, ask_price = get_market_prices(symbol, market_trend)
        price_history.append(bid_price)  # Track bid prices for mean reversion
        prices.append(bid_price)  # Track prices for technical indicators

        # Ensure bid price is less than or equal to ask price
        if bid_price <= ask_price:
            spread = ask_price - bid_price

            # Mean Reversion Strategy
            mean_reversion_action = mean_reversion_strategy(list(price_history))
            if mean_reversion_action == 'BUY':
                print("Mean Reversion Strategy suggests buying.")
                order_price, transaction_cost = place_order('BUY', symbol, bid_price, 1)
                current_capital -= (order_price + transaction_cost)
                shares_held += 1
                print(f"Shares held after buying: {shares_held}")

            elif mean_reversion_action == 'SELL':
                print("Mean Reversion Strategy suggests selling.")
                if shares_held > 0:
                    order_price, transaction_cost = place_order('SELL', symbol, ask_price, 1)
                    current_capital += (order_price - transaction_cost)
                    shares_held -= 1
                    print(f"Shares held after selling: {shares_held}")

            # Calculate Moving Average
            ma = moving_average(prices)

            # Trading logic based on Moving Average
            if ma is not None:
                if bid_price < ma:
                    print("Bid price is below Moving Average. Suggesting to buy.")
                    order_price, transaction_cost = place_order('BUY', symbol, bid_price, 1)
                    current_capital -= (order_price + transaction_cost)
                    shares_held += 1
                    print(f"Shares held after buying: {shares_held}")

                elif bid_price > ma:
                    print("Bid price is above Moving Average. Suggesting to sell.")
                    if shares_held > 0:
                        order_price, transaction_cost = place_order('SELL', symbol, ask_price, 1)
                        current_capital += (order_price - transaction_cost)
                        shares_held -= 1
                        print(f"Shares held after selling: {shares_held}")

            # Random event that can negatively impact the market
            if random.random() < 0.2:  # 20% chance of a bad event
                market_trend = random.choice([-0.2, -0.25])  # Sudden downturn
                print("Market downturn event triggered! Adjusting trend.")

            # Implementing exit strategy with condition to sell remaining shares
            if exit_strategy(current_capital, shares_held, bid_price, initial_capital):
                if shares_held > 0:
                    print("Selling remaining shares before exiting due to profit/loss threshold.")
                    order_price, transaction_cost = place_order('SELL', symbol, bid_price, shares_held)  # Sell all remaining shares
                    current_capital += (order_price * shares_held - transaction_cost)  # Add value of sold shares minus transaction cost
                    shares_held = 0  # Reset shares held to zero
                break

        # Time-based exit strategy (HFT holds for very short periods)
        current_time = time.time()
        if current_time - start_time > 2:  # Exit after holding for 2 seconds
            print("Time-based exit strategy triggered. Exiting positions.")
            if shares_held > 0:
                order_price, transaction_cost = place_order('SELL', symbol, bid_price, shares_held)  # Sell all remaining shares
                current_capital += (order_price * shares_held - transaction_cost)  # Add the value of all sold shares minus transaction cost
                shares_held = 0  # Reset shares held to zero
            break

        time.sleep(0.01)  # Adjust time interval for HFT, typically very short

    # Print final profit/loss
    total_value = current_capital + (shares_held * bid_price)  # Total value including held shares
    profit_loss = total_value - initial_capital  # Calculate profit/loss
    print(f"Final Capital: {current_capital:.2f} | Profit/Loss: {profit_loss:.2f} | Final Shares Held: {shares_held}")

# Example usage
if __name__ == "__main__":
    market_maker("ArthaVedh", desired_spread=2.0)
