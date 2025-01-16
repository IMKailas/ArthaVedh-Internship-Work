import random
import time
import logging
from collections import deque
import config

# Configure logging
logging.basicConfig(
    filename=config.LOG_FILE,
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

def get_market_prices(symbol, trend=0):
    base_price = random.uniform(config.BASE_PRICE_MIN, config.BASE_PRICE_MAX)
    shock = random.uniform(config.SHOCK_RANGE_MIN, config.SHOCK_RANGE_MAX)
    price_change = trend + shock
    bid_price = round(base_price + price_change, 2)
    ask_price = round(bid_price + random.uniform(config.ASK_PRICE_MIN_SPREAD, config.ASK_PRICE_MAX_SPREAD), 2)
    return bid_price, ask_price

def place_order(order_type, symbol, price, shares_count):
    transaction_cost = config.TRANSACTION_COST_PERCENTAGE * price * shares_count
    slippage = random.uniform(config.SLIPPAGE_RANGE_MIN, config.SLIPPAGE_RANGE_MAX)
    final_price = price + slippage
    logger.info(f"Placed {order_type} order for {shares_count} shares of {symbol} at {final_price:.2f} (Slippage: {slippage:.2f}) | Transaction cost: {transaction_cost:.2f}")
    return final_price, transaction_cost

def moving_average(prices, period=config.MOVING_AVERAGE_PERIOD):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def mean_reversion_strategy(prices, threshold=config.MEAN_REVERSION_THRESHOLD):
    if len(prices) < 5:
        return None

    mean_price = sum(prices) / len(prices)
    current_price = prices[-1]
    deviation = current_price - mean_price

    if deviation > threshold:
        return 'SELL'
    elif deviation < -threshold:
        return 'BUY'
    return None

def exit_strategy(current_capital, shares_held, bid_price, initial_capital, max_profit=config.MAX_PROFIT_LIMIT, max_loss=config.MAX_LOSS_LIMIT):
    total_value = current_capital + (shares_held * bid_price)
    profit_loss = total_value - initial_capital

    if profit_loss >= max_profit:
        logger.info(f"Profit target reached: {profit_loss:.2f}. Exiting all positions.")
        return True
    if profit_loss <= max_loss:
        logger.info(f"Loss limit reached: {profit_loss:.2f}. Exiting all positions.")
        return True

    return False

def market_maker(symbol, desired_spread):
    price_history = deque(maxlen=config.PRICE_HISTORY_LENGTH)
    prices = []

    initial_capital = config.INITIAL_CAPITAL
    current_capital = initial_capital
    shares_held = 0

    market_trend = random.choice(config.MARKET_TRENDS)
    logger.info(f"Starting market maker with initial capital: {initial_capital}, symbol: {symbol}")

    start_time = time.time()

    while True:
        bid_price, ask_price = get_market_prices(symbol, market_trend)
        price_history.append(bid_price)
        prices.append(bid_price)

        if bid_price <= ask_price:
            spread = ask_price - bid_price

            mean_reversion_action = mean_reversion_strategy(list(price_history))
            if mean_reversion_action == 'BUY':
                logger.info("Mean Reversion Strategy suggests buying.")
                order_price, transaction_cost = place_order('BUY', symbol, bid_price, 1)
                current_capital -= (order_price + transaction_cost)
                shares_held += 1
                logger.info(f"Shares held after buying: {shares_held}")

            elif mean_reversion_action == 'SELL':
                logger.info("Mean Reversion Strategy suggests selling.")
                if shares_held > 0:
                    order_price, transaction_cost = place_order('SELL', symbol, ask_price, 1)
                    current_capital += (order_price - transaction_cost)
                    shares_held -= 1
                    logger.info(f"Shares held after selling: {shares_held}")

            ma = moving_average(prices)

            if ma is not None:
                if bid_price < ma:
                    logger.info("Bid price is below Moving Average. Suggesting to buy.")
                    order_price, transaction_cost = place_order('BUY', symbol, bid_price, 1)
                    current_capital -= (order_price + transaction_cost)
                    shares_held += 1
                    logger.info(f"Shares held after buying: {shares_held}")

                elif bid_price > ma:
                    logger.info("Bid price is above Moving Average. Suggesting to sell.")
                    if shares_held > 0:
                        order_price, transaction_cost = place_order('SELL', symbol, ask_price, 1)
                        current_capital += (order_price - transaction_cost)
                        shares_held -= 1
                        logger.info(f"Shares held after selling: {shares_held}")

            if random.random() < config.MARKET_DOWNTURN_PROBABILITY:
                market_trend = random.choice(config.MARKET_DOWNTURN_TRENDS)
                logger.warning("Market downturn event triggered! Adjusting trend.")

            if exit_strategy(current_capital, shares_held, bid_price, initial_capital):
                if shares_held > 0:
                    logger.info("Selling remaining shares before exiting due to profit/loss threshold.")
                    order_price, transaction_cost = place_order('SELL', symbol, bid_price, shares_held)
                    current_capital += (order_price * shares_held - transaction_cost)
                    shares_held = 0
                break

        current_time = time.time()
        if current_time - start_time > config.HOLDING_PERIOD:
            logger.info("Time-based exit strategy triggered. Exiting positions.")
            if shares_held > 0:
                order_price, transaction_cost = place_order('SELL', symbol, bid_price, shares_held)
                current_capital += (order_price * shares_held - transaction_cost)
                shares_held = 0
            break

        time.sleep(config.TRADING_INTERVAL)

    total_value = current_capital + (shares_held * bid_price)
    profit_loss = total_value - initial_capital
    logger.info(f"Final Capital: {current_capital:.2f} | Profit/Loss: {profit_loss:.2f} | Final Shares Held: {shares_held}")

if __name__ == "__main__":
    market_maker(config.SYMBOL, config.DESIRED_SPREAD)