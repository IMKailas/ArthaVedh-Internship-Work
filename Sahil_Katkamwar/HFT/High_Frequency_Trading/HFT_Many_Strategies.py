# Key HFT Strategies to Implement

# Market Making:
# Continuously placing buy and sell orders at specified prices to profit
# from the bid-ask spread.

# Mean Reversion:
# This strategy assumes that asset prices will revert to their historical mean.
# You can monitor the price deviation from its moving average and place trades
# when the price is significantly away from the mean.

# Arbitrage:
# This involves exploiting price differences of the same asset across
# different markets or exchanges. If the asset is available at a lower price in one market
# and higher in another, you can buy low and sell high.

# Volume Analysis:
# Analyzing trading volume can provide insights into market movements.
# Increased volume might indicate a price change, allowing the algorithm to adapt
# its strategy accordingly.

# Technical Indicators:
# Incorporate common technical indicators like Moving Averages (MA),
# Relative Strength Index (RSI), Bollinger Bands, etc., to guide trading decisions.

import random
import time
from collections import deque
from textblob import TextBlob
import threading
import keyboard  # For capturing keyboard events


# Simulated function to get market prices
# Mock data : Replace this with API call to get current market status
def get_market_prices(symbol):
    bid_price = round(random.uniform(100, 200), 2)
    ask_price = round(bid_price + random.uniform(0.01, 5), 2)
    return bid_price, ask_price


# Simulated function to fetch recent news about ArthaVedh
def fetch_recent_news(symbol):
    articles = [
        "ArthaVedh announces record profits and growth in Q3.",
        "ArthaVedh faces legal challenges that may impact stock value.",
        "ArthaVedh's new product launch has received positive feedback from consumers.",
        "ArthaVedh reports a major data breach, raising security concerns.",
        "ArthaVedh signs a strategic partnership with a leading firm.",
        "Analysts predict a bullish outlook for ArthaVedh following strong sales figures.",
        "ArthaVedh experiences a significant drop in stock price due to market volatility.",
        "Investors are optimistic about ArthaVedh's expansion plans in the tech sector.",
        "ArthaVedh's CEO faces scrutiny over questionable business practices, impacting investor confidence.",
        "Analysts downgrade ArthaVedh's stock rating amid declining sales and increasing competition.",
        "ArthaVedh reports a significant drop in revenue, leading to concerns about future profitability.",
        "Investor sentiment wanes as ArthaVedh fails to meet quarterly earnings expectations.",
        "ArthaVedh's recent merger raises red flags, with analysts predicting potential integration challenges.",
        "Negative press coverage surrounding ArthaVedh's management decisions affects stock performance.",
        "ArthaVedh's failure to innovate could lead to a loss of market share in the coming years.",
        "Legal issues surrounding ArthaVedh may result in hefty fines and operational disruptions."
    ]
    return random.choice(articles)


# Function to analyze sentiment
def analyze_sentiment(news_article):
    analysis = TextBlob(news_article)
    return analysis.sentiment.polarity  # Returns a value between -1 (negative) and 1 (positive)


# Simulated function to place an order
def place_order(order_type, symbol, price):
    print(f"Placed {order_type} order for {symbol} at {price}")
    return price  # Return the price for profit/loss calculation


# Function to calculate moving average
def moving_average(prices, period=5):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


# Function to calculate Relative Strength Index (RSI)
def qcalculate_rsi(prices, period=14):
    if len(prices) < period:
        return None
    gains = [max(prices[i] - prices[i - 1], 0) for i in range(1, len(prices))]
    losses = [max(prices[i - 1] - prices[i], 0) for i in range(1, len(prices))]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Function for mean reversion strategy
def mean_reversion_strategy(prices, threshold=2.0):
    if len(prices) < 5:
        return None  # Not enough data to calculate mean

    mean_price = sum(prices) / len(prices)
    current_price = prices[-1]
    deviation = current_price - mean_price

    if deviation > threshold:
        return 'SELL'  # Price is significantly above mean
    elif deviation < -threshold:
        return 'BUY'  # Price is significantly below mean
    return None  # No action


def stop_trading():
    while True:
        if keyboard.is_pressed('q'):  # Stop if 'q' is pressed
            print("Exiting trading...")
            break

# Market maker function
def market_maker(symbol, desired_spread):
    buy_orders = deque(maxlen=100)
    sell_orders = deque(maxlen=100)
    price_history = deque(maxlen=50)  # Store last 50 prices for mean reversion
    prices = []  # Store historical prices for technical indicators

    initial_capital = 100000  # Starting capital
    current_capital = initial_capital
    shares_held = 0  # Track shares held

    # Start the thread to capture keyboard input
    threading.Thread(target=stop_trading, daemon=True).start()

    while True:
        bid_price, ask_price = get_market_prices(symbol)
        price_history.append(bid_price)  # Track bid prices for mean reversion
        prices.append(bid_price)  # Track prices for technical indicators

        # Fetch and analyze recent news about ArthaVedh
        news_article = fetch_recent_news(symbol)
        sentiment_score = analyze_sentiment(news_article)

        # Print fetched news and sentiment score
        print(f"News: {news_article} | Sentiment Score: {sentiment_score:.2f}")

        # Ensure bid price is less than or equal to ask price
        if bid_price <= ask_price:
            spread = ask_price - bid_price

            # Adjust trading strategy based on sentiment
            if sentiment_score > 0.1:  # Positive sentiment
                print("Positive sentiment detected. Suggesting to buy.")
                if spread < desired_spread:
                    order_price = place_order('BUY', symbol, bid_price)
                    current_capital -= order_price  # Deduct the cost of buying
                    shares_held += 1  # Track shares held
                    buy_orders.append(order_price)
                    sell_orders.append(ask_price)

            elif sentiment_score < -0.1:  # Negative sentiment
                print("Negative sentiment detected. Suggesting to sell.")
                if shares_held > 0:  # Only sell if we have shares
                    order_price = place_order('SELL', symbol, ask_price)
                    current_capital += order_price  # Add to capital from selling
                    shares_held -= 1  # Reduce shares held

            # Mean Reversion Strategy
            mean_reversion_action = mean_reversion_strategy(list(price_history))
            if mean_reversion_action == 'BUY':
                print("Mean Reversion Strategy suggests buying.")
                order_price = place_order('BUY', symbol, bid_price)
                current_capital -= order_price
                shares_held += 1

            elif mean_reversion_action == 'SELL':
                print("Mean Reversion Strategy suggests selling.")
                if shares_held > 0:
                    order_price = place_order('SELL', symbol, ask_price)
                    current_capital += order_price
                    shares_held -= 1

            # Calculate Technical Indicators
            ma = moving_average(prices)
            rsi = calculate_rsi(prices)

            # Trading logic based on Moving Average
            if ma is not None:
                if bid_price < ma:
                    print("Bid price is below Moving Average. Suggesting to buy.")
                    order_price = place_order('BUY', symbol, bid_price)
                    current_capital -= order_price
                    shares_held += 1

                elif bid_price > ma:
                    print("Bid price is above Moving Average. Suggesting to sell.")
                    if shares_held > 0:
                        order_price = place_order('SELL', symbol, ask_price)
                        current_capital += order_price
                        shares_held -= 1

            # Trading logic based on RSI
            if rsi is not None:
                print(f"RSI: {rsi:.2f}")
                if rsi < 30:
                    print("RSI indicates oversold condition. Suggesting to buy.")
                    order_price = place_order('BUY', symbol, bid_price)
                    current_capital -= order_price
                    shares_held += 1

                elif rsi > 70:
                    print("RSI indicates overbought condition. Suggesting to sell.")
                    if shares_held > 0:
                        order_price = place_order('SELL', symbol, ask_price)
                        current_capital += order_price
                        shares_held -= 1

        # Print current capital and profit/loss
        total_value = current_capital + (shares_held * bid_price)  # Total value including held shares
        profit_loss = total_value - initial_capital  # Calculate profit/loss
        print(
            f"Current Capital: {current_capital:.2f} | Total Value: {total_value:.2f} | Profit/Loss: {profit_loss:.2f}")

        if keyboard.is_pressed('q'):
            print("Exiting trading...")
            break

        time.sleep(0.5)  # Adjust sleep time as needed


# Example usage
if __name__ == "__main__":
    market_maker("ArthaVedh", desired_spread=2.0)
