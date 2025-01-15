# straddle_strategy.py

import time
from market_data import get_market_data, simulate_price_change
import config

def straddle_decision(market_data):
    """Calculate straddle strategy decision based on market data"""
    spread = market_data["ask_price"] - market_data["bid_price"]
    
    print(f"Bid: {market_data['bid_price']}, "
          f"Ask: {market_data['ask_price']}, "
          f"Spread: {spread:.2f}, "
          f"IV: {market_data['implied_volatility']}, "
          f"Delta: {market_data['delta']:.2f}, "
          f"Volume: {market_data['volume']}")

    if (spread <= config.STRADDLE_PARAMS["MAX_SPREAD"] and 
        market_data["volume"] >= config.STRADDLE_PARAMS["MIN_VOLUME"] and 
        market_data["implied_volatility"] >= config.STRADDLE_PARAMS["MIN_IMPLIED_VOLATILITY"]):
        if market_data["delta"] > 0:
            return "Buy Call & Put"
    return "Hold"

def run_straddle_strategy():
    balance = config.INITIAL_BALANCE
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None

    while True:
        market_data = get_market_data(strategy_type="straddle")

        if position is None:
            decision = straddle_decision(market_data)

            if decision == "Buy Call & Put":
                position = "Buy Call & Put"
                trade_price = market_data["ask_price"]
                stop_loss = trade_price * (1 - config.STOP_LOSS_PCT / 100)
                target_profit = trade_price * (1 + config.TARGET_PROFIT_PCT / 100)
                print(f"Entering Straddle at {trade_price} "
                      f"with Stop Loss at {stop_loss} "
                      f"and Target at {target_profit}")

        if position is not None:
            current_price = simulate_price_change(trade_price, "Buy")

            if current_price <= stop_loss:
                print(f"Stop Loss hit on Straddle! Exiting trade at {current_price}")
                balance -= (trade_price - current_price)
                position = None
            elif current_price >= target_profit:
                print(f"Target Profit reached on Straddle! Exiting trade at {current_price}")
                balance += (current_price - trade_price)
                position = None

            print(f"Current Price: {current_price}, Balance: {balance:.2f}")

            if balance <= config.INITIAL_BALANCE * config.BALANCE_RISK_THRESHOLD:
                print(f"Balance dropped below {config.BALANCE_RISK_THRESHOLD*100}% "
                      f"of initial value. Stopping strategy.")
                break

        time.sleep(config.UPDATE_INTERVAL)
