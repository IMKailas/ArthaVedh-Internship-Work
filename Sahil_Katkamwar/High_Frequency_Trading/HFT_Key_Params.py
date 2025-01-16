import random
import time
from collections import deque


# Simulated function to get market prices
# Mock data : Replace this with API call to get current market status
def get_market_prices(symbol):
    # Simulating bid and ask prices
    bid_price = round(random.uniform(100, 200), 2)  # Random bid price between 100 and 200
    ask_price = round(bid_price + random.uniform(0.01, 5), 2)  # Random ask price slightly above bid
    return bid_price, ask_price


# Simulated function to place an order
def place_order(order_type, symbol, price):
    print(f"Placed {order_type} order for {symbol} at {price}")


# Market maker function
def market_maker(symbol, desired_spread):
    # Deques to track order flow
    buy_orders = deque(maxlen=100)  # Track the last 100 buy orders
    sell_orders = deque(maxlen=100)  # Track the last 100 sell orders

    while True:
        bid_price, ask_price = get_market_prices(symbol)

        # Ensure bid price is less than or equal to ask price
        if bid_price <= ask_price:
            spread = ask_price - bid_price

            # Check if the spread is less than the desired spread
            if spread < desired_spread:
                # Place buy and sell orders
                place_order('BUY', symbol, bid_price)
                place_order('SELL', symbol, ask_price)

                # Track order flow
                buy_orders.append(bid_price)
                sell_orders.append(ask_price)

                # Analyze order flow
                analyze_order_flow(buy_orders, sell_orders)
            else:
                # Log the situation or take other actions
                print(f"Spread too large: {spread:.2f}, not placing orders.")

        # Sleep for a short time to avoid overwhelming the market
        time.sleep(1)  # Adjust sleep time as needed


def analyze_order_flow(buy_orders, sell_orders):
    # Simple analysis of order flow
    avg_buy_price = sum(buy_orders) / len(buy_orders) if buy_orders else 0
    avg_sell_price = sum(sell_orders) / len(sell_orders) if sell_orders else 0

    print(f"Average Buy Price: {avg_buy_price:.2f}, Average Sell Price: {avg_sell_price:.2f}")


# Example usage
if __name__ == "__main__":
    market_maker("Arthavedh", desired_spread=2.0)
