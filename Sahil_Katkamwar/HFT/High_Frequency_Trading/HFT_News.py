import random
import time
from collections import deque
from textblob import TextBlob  # Simple sentiment analysis library


# Simulated function to get market prices
# Mock data : Replace this with API call to get current market status
def get_market_prices(symbol):
    bid_price = round(random.uniform(100, 200), 2)
    ask_price = round(bid_price + random.uniform(0.01, 5), 2)
    return bid_price, ask_price


# Simulated function to fetch recent news
def fetch_recent_news(symbol):
    articles = [
        "Company X announces record profits and growth in Q3.",
        "Company Y faces legal challenges that may impact stock value.",
        "New product launch has received positive feedback from consumers.",
        "Company Z reports a major data breach, raising security concerns.",
        "Company A signs a strategic partnership with a leading firm."
    ]
    return random.choice(articles)


# Function to analyze sentiment
def analyze_sentiment(news_article):
    analysis = TextBlob(news_article)
    return analysis.sentiment.polarity  # Returns a value between -1 (negative) and 1 (positive)


# Simulated function to place an order
def place_order(order_type, symbol, price):
    print(f"Placed {order_type} order for {symbol} at {price}")


# Market maker function
def market_maker(symbol, desired_spread):
    buy_orders = deque(maxlen=100)
    sell_orders = deque(maxlen=100)

    while True:
        bid_price, ask_price = get_market_prices(symbol)

        # Fetch and analyze recent news
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
                    place_order('BUY', symbol, bid_price)
                    place_order('SELL', symbol, ask_price)
                    buy_orders.append(bid_price)
                    sell_orders.append(ask_price)
            elif sentiment_score < -0.1:  # Negative sentiment
                print("Negative sentiment detected. Suggesting to sell.")
                # You can implement selling logic or avoid placing new buy orders.
            else:
                print("Neutral sentiment detected. No action recommended.")

        time.sleep(1)  # Adjust sleep time as needed


# Example usage
if __name__ == "__main__":
    market_maker("Arthavedh", desired_spread=2.0)
