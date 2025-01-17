
# strangle_strategy.py

import time
import config

def strangle_decision(market_data):
    """Calculate strangle strategy decision based on market data"""
    if market_data is None:
        return "Hold"
        
    spread = market_data["spread"]
    volume = market_data["volume"]
    volume_ma = market_data["volume_ma"]
    stoch_k = market_data["stoch_k"]
    stoch_d = market_data["stoch_d"]
    
    # Calculate volume ratio for signal confirmation
    volume_ratio = volume / volume_ma if volume_ma > 0 else 0

    print(f"Time: {market_data['timestamp']}, "
          f"Price: {market_data['current_price']}, "
          f"Spread: {spread:.2f}, "
          f"Volume: {volume}, "
          f"Volume Ratio: {volume_ratio:.2f}")

    if (spread <= config.STRANGLE_PARAMS["MAX_SPREAD"] and 
        volume >= config.STRANGLE_PARAMS["MIN_VOLUME"] and
        volume_ratio >= config.STRANGLE_PARAMS["VOLUME_MA_MULTIPLIER"] and
        stoch_k > stoch_d):  # Additional confirmation using stochastic
        return "Buy Call and Buy Put"
    return "Hold"

def run_strangle_strategy(market_data_manager):
    """Run strangle strategy with real market data"""
    balance = config.INITIAL_BALANCE
    position = None
    call_entry_price = None
    put_entry_price = None
    stop_loss_call = None
    stop_loss_put = None
    target_profit_call = None
    target_profit_put = None

    while market_data_manager.is_data_available():
        market_data = market_data_manager.get_current_market_data(strategy_type="strangle")
        
        if market_data is None:
            break

        if position is None:
            decision = strangle_decision(market_data)

            if decision == "Buy Call and Buy Put":
                position = "Strangle"
                call_entry_price = market_data["ask_price"]
                put_entry_price = market_data["bid_price"]
                stop_loss_call = call_entry_price * (1 - config.STOP_LOSS_PCT / 100)
                stop_loss_put = put_entry_price * (1 + config.STOP_LOSS_PCT / 100)
                target_profit_call = call_entry_price * (1 + config.TARGET_PROFIT_PCT / 100)
                target_profit_put = put_entry_price * (1 - config.TARGET_PROFIT_PCT / 100)
                print(f"Entering Strangle: Buy Call at {call_entry_price}, "
                      f"Buy Put at {put_entry_price}")

        if position == "Strangle":
            current_price = market_data["current_price"]
            
            # Check call option conditions
            if current_price >= target_profit_call:
                print(f"Target Profit reached on Call! Exiting at {current_price}")
                balance += (current_price - call_entry_price)
                position = None
            elif current_price <= stop_loss_call:
                print(f"Stop Loss hit on Call! Exiting at {current_price}")
                balance -= (call_entry_price - current_price)
                position = None

            # Check put option conditions
            if current_price <= target_profit_put:
                print(f"Target Profit reached on Put! Exiting at {current_price}")
                balance += (put_entry_price - current_price)
                position = None
            elif current_price >= stop_loss_put:
                print(f"Stop Loss hit on Put! Exiting at {current_price}")
                balance -= (current_price - put_entry_price)
                position = None

            print(f"Current Price: {current_price}, Balance: {balance:.2f}")

            if balance <= config.INITIAL_BALANCE * config.BALANCE_RISK_THRESHOLD:
                print(f"Balance dropped below {config.BALANCE_RISK_THRESHOLD*100}% "
                      f"of initial value. Stopping strategy.")
                break

        market_data_manager.advance()
        time.sleep(config.UPDATE_INTERVAL)
    
    return balance
