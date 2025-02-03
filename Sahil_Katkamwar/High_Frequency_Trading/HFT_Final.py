import random
import time
import logging
from collections import deque
import numpy as np
import talib
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
    logger.info(
        f"Placed {order_type} order for {shares_count} shares of {symbol} at {final_price:.2f} (Slippage: {slippage:.2f}) | Transaction cost: {transaction_cost:.2f}")
    return final_price, transaction_cost


def calculate_technical_indicators(prices):
    """Calculate technical indicators using TA-Lib"""
    # Convert prices to numpy array
    prices_array = np.array(prices)

    # Calculate Simple Moving Average
    sma = talib.SMA(prices_array, timeperiod=config.MOVING_AVERAGE_PERIOD)

    # Calculate RSI
    rsi = talib.RSI(prices_array, timeperiod=14)

    # Calculate MACD
    macd, macd_signal, macd_hist = talib.MACD(
        prices_array,
        fastperiod=12,
        slowperiod=26,
        signalperiod=9
    )

    return {
        'sma': sma,
        'rsi': rsi,
        'macd': macd,
        'macd_signal': macd_signal,
        'macd_hist': macd_hist
    }


def mean_reversion_strategy(prices, indicators, threshold=config.MEAN_REVERSION_THRESHOLD):
    if len(prices) < 5:
        return None

    mean_price = indicators['sma'][-1]
    current_price = prices[-1]
    deviation = current_price - mean_price

    # Enhanced strategy using RSI and MACD
    rsi = indicators['rsi'][-1]
    macd = indicators['macd'][-1]
    macd_signal = indicators['macd_signal'][-1]

    # Combine mean reversion with RSI and MACD confirmation
    if deviation > threshold and rsi > 70 and macd < macd_signal:
        return 'SELL'
    elif deviation < -threshold and rsi < 30 and macd > macd_signal:
        return 'BUY'

    return None


def exit_strategy(current_capital, shares_held, bid_price, initial_capital, max_profit=config.MAX_PROFIT_LIMIT,
                  max_loss=config.MAX_LOSS_LIMIT):
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
            # Calculate technical indicators
            indicators = calculate_technical_indicators(prices)

            # Mean reversion strategy with enhanced indicators
            mean_reversion_action = mean_reversion_strategy(prices, indicators)

            if mean_reversion_action == 'BUY':
                logger.info("Enhanced Mean Reversion Strategy suggests buying.")
                order_price, transaction_cost = place_order('BUY', symbol, bid_price, 1)
                current_capital -= (order_price + transaction_cost)
                shares_held += 1
                logger.info(f"Shares held after buying: {shares_held}")

            elif mean_reversion_action == 'SELL':
                logger.info("Enhanced Mean Reversion Strategy suggests selling.")
                if shares_held > 0:
                    order_price, transaction_cost = place_order('SELL', symbol, ask_price, 1)
                    current_capital += (order_price - transaction_cost)
                    shares_held -= 1
                    logger.info(f"Shares held after selling: {shares_held}")

            # Moving average-based strategy
            ma = indicators['sma'][-1] if indicators['sma'][-1] is not np.nan else None

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

            # Market trend randomization
            if random.random() < config.MARKET_DOWNTURN_PROBABILITY:
                market_trend = random.choice(config.MARKET_DOWNTURN_TRENDS)
                logger.warning("Market downturn event triggered! Adjusting trend.")

            # Exit strategy
            if exit_strategy(current_capital, shares_held, bid_price, initial_capital):
                if shares_held > 0:
                    logger.info("Selling remaining shares before exiting due to profit/loss threshold.")
                    order_price, transaction_cost = place_order('SELL', symbol, bid_price, shares_held)
                    current_capital += (order_price * shares_held - transaction_cost)
                    shares_held = 0
                break

        # Time-based exit
        current_time = time.time()
        if current_time - start_time > config.HOLDING_PERIOD:
            logger.info("Time-based exit strategy triggered. Exiting positions.")
            if shares_held > 0:
                order_price, transaction_cost = place_order('SELL', symbol, bid_price, shares_held)
                current_capital += (order_price * shares_held - transaction_cost)
                shares_held = 0
            break

        time.sleep(config.TRADING_INTERVAL)

    # Final reporting
    total_value = current_capital + (shares_held * bid_price)
    profit_loss = total_value - initial_capital
    logger.info(
        f"Final Capital: {current_capital:.2f} | Profit/Loss: {profit_loss:.2f} | Final Shares Held: {shares_held}")


if __name__ == "__main__":
    market_maker(config.SYMBOL, config.DESIRED_SPREAD)