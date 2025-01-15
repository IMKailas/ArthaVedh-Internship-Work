# market_data.py

import random
import config

def get_market_data(strategy_type="straddle"):
    """
    Get simulated market data based on strategy type
    """
    market_data = {
        "bid_price": round(random.uniform(config.PRICE_RANGE["MIN_BID"], 
                                        config.PRICE_RANGE["MAX_BID"]), 2),
        "ask_price": round(random.uniform(config.PRICE_RANGE["MIN_ASK"], 
                                        config.PRICE_RANGE["MAX_ASK"]), 2),
        "volume": random.randint(config.VOLUME_RANGE["MIN"], 
                               config.VOLUME_RANGE["MAX"]),
        "buy_orders": random.randint(config.ORDER_FLOW_RANGE["MIN"], 
                                   config.ORDER_FLOW_RANGE["MAX"]),
        "sell_orders": random.randint(config.ORDER_FLOW_RANGE["MIN"], 
                                    config.ORDER_FLOW_RANGE["MAX"])
    }
    
    # Add straddle-specific data if needed
    if strategy_type == "straddle":
        market_data.update({
            "implied_volatility": round(
                random.uniform(
                    config.STRADDLE_PARAMS["IMPLIED_VOLATILITY_RANGE"]["MIN"],
                    config.STRADDLE_PARAMS["IMPLIED_VOLATILITY_RANGE"]["MAX"]
                ), 2
            ),
            "delta": round(
                random.uniform(
                    config.STRADDLE_PARAMS["DELTA_RANGE"]["MIN"],
                    config.STRADDLE_PARAMS["DELTA_RANGE"]["MAX"]
                ), 2
            )
        })
    
    return market_data

def simulate_price_change(entry_price, direction):
    """
    Simulate price changes for both strategies
    """
    change = random.uniform(config.PRICE_SIMULATION["MIN_CHANGE"], 
                          config.PRICE_SIMULATION["MAX_CHANGE"])
    
    if direction in ["Buy", "Call"]:
        return round(entry_price + change, 2)
    elif direction in ["Sell", "Put"]:
        return round(entry_price - change, 2)
    
    return entry_price
