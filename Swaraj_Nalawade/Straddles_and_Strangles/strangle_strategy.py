# strangle_strategy.py

import time
from market_data import get_market_data, simulate_price_change
import config

def strangle_decision(market_data):
    """Calculate strangle strategy decision based on market data"""
    spread = market_data["ask_price"] - market_data["bid_price"]
    order_flow_ratio = (market_data["buy_orders"] / market_data["sell_orders"] 
                       if market_data["sell_orders"] > 0 else float('inf'))

    print(f"Bid: {market_data['bid_price']}, "
          f"Ask: {market_data['ask_price']}, "
          f"Spread: {spread:.2f}, "
          f"Volume: {market_data['volume']}, "
          f"Order Flow Ratio: {order_flow_ratio:.2f}")

    if (spread <= config.STRANGLE_PARAMS["MAX_SPREAD"] and 
        market_data["volume"] >= config.STRANGLE_PARAMS["MIN_VOLUME"] and
        order_flow_ratio >= config.STRANGLE_PARAMS["MIN_ORDER_FLOW_RATIO"]):
        return "Buy Call and Buy Put"
    return "Hold"

def run_strangle_strategy():
    balance = config.INITIAL_BALANCE
    position = None
    call_price = None
    put_price = None
    stop_loss_call = None
    stop_loss_put = None
    target_profit_call = None
    target_profit_put = None

    while True:
        market_data = get_market_data(strategy_type="strangle")

        if position is None:
            decision = strangle_decision(market_data)

            if decision == "Buy Call and Buy Put":
                position = "Strangle"
                call_price = market_data["ask_price"]
                put_price = market_data["bid_price"]
                stop_loss_call = call_price * (1 - config.STOP_LOSS_PCT / 100)
                stop_loss_put = put_price * (1 + config.STOP_LOSS_PCT / 100)
                target_profit_call = call_price * (1 + config.TARGET_PROFIT_PCT / 100)
                target_profit_put = put_price * (1 - config.TARGET_PROFIT_PCT / 100)
                print(f"Entering Strangle: Buy Call at {call_price}, "
                      f"Buy Put at {put_price}")

        if position == "Strangle":
            call_current_price = simulate_price_change(call_price, "Call")
            put_current_price = simulate_price_change(put_price, "Put")
            
            # Check call option conditions
            if call_current_price >= target_profit_call:
                print(f"Target Profit reached on Call! Exiting at {call_current_price}")
                balance += (call_current_price - call_price)
                position = None
            elif call_current_price <= stop_loss_call:
                print(f"Stop Loss hit on Call! Exiting at {call_current_price}")
                balance -= (call_price - call_current_price)
                position = None

            # Check put option conditions
            if put_current_price <= target_profit_put:
                print(f"Target Profit reached on Put! Exiting at {put_current_price}")
                balance += (put_price - put_current_price)
                position = None
            elif put_current_price >= stop_loss_put:
                print(f"Stop Loss hit on Put! Exiting at {put_current_price}")
                balance -= (put_current_price - put_price)
                position = None

            print(f"Call Price: {call_current_price}, "
                  f"Put Price: {put_current_price}, "
                  f"Balance: {balance:.2f}")

            if balance <= config.INITIAL_BALANCE * config.BALANCE_RISK_THRESHOLD:
                print(f"Balance dropped below {config.BALANCE_RISK_THRESHOLD*100}% "
                      f"of initial value. Stopping strategy.")
                break

        time.sleep(config.UPDATE_INTERVAL)
