
# straddle_strategy.py

import time
import config

def straddle_decision(market_data):
    """Calculate straddle strategy decision based on market data"""
    if market_data is None:
        return "Hold"
        
    spread = market_data["spread"]
    volume = market_data["volume"]
    rsi = market_data["rsi"]
    delta = market_data["delta"]
    
    print(f"Time: {market_data['timestamp']}, "
          f"Price: {market_data['current_price']}, "
          f"Spread: {spread:.2f}, "
          f"RSI: {rsi:.2f}, "
          f"Delta: {delta:.2f}, "
          f"Volume: {volume}")

    # Entry conditions using RSI as volatility indicator
    if (spread <= config.STRADDLE_PARAMS["MAX_SPREAD"] and 
        volume >= config.STRADDLE_PARAMS["MIN_VOLUME"] and 
        rsi <= config.STRADDLE_PARAMS["RSI_OVERSOLD"] or 
        rsi >= config.STRADDLE_PARAMS["RSI_OVERBOUGHT"]):
        return "Buy Call & Put"
    return "Hold"

def run_straddle_strategy(market_data_manager):
    """Run straddle strategy with real market data"""
    balance = config.INITIAL_BALANCE
    position = None
    entry_price = None
    stop_loss = None
    target_profit = None

    while market_data_manager.is_data_available():
        market_data = market_data_manager.get_current_market_data(strategy_type="straddle")
        
        if market_data is None:
            break

        if position is None:
            decision = straddle_decision(market_data)

            if decision == "Buy Call & Put":
                position = "Buy Call & Put"
                entry_price = market_data["current_price"]
                stop_loss = entry_price * (1 - config.STOP_LOSS_PCT / 100)
                target_profit = entry_price * (1 + config.TARGET_PROFIT_PCT / 100)
                print(f"Entering Straddle at {entry_price} "
                      f"with Stop Loss at {stop_loss} "
                      f"and Target at {target_profit}")

        if position is not None:
            current_price = market_data["current_price"]

            if current_price <= stop_loss:
                print(f"Stop Loss hit on Straddle! Exiting trade at {current_price}")
                balance -= (entry_price - current_price)
                position = None
            elif current_price >= target_profit:
                print(f"Target Profit reached on Straddle! Exiting trade at {current_price}")
                balance += (current_price - entry_price)
                position = None

            print(f"Current Price: {current_price}, Balance: {balance:.2f}")

            if balance <= config.INITIAL_BALANCE * config.BALANCE_RISK_THRESHOLD:
                print(f"Balance dropped below {config.BALANCE_RISK_THRESHOLD*100}% "
                      f"of initial value. Stopping strategy.")
                break

        market_data_manager.advance()
        time.sleep(config.UPDATE_INTERVAL)
    
    return balance
