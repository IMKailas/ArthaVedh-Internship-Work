
# market_data.py

import pandas as pd
from datetime import datetime
import config

class MarketDataManager:
    def __init__(self, csv_file):
        """Initialize the market data manager with CSV file"""
        self.df = pd.read_csv(csv_file, parse_dates=['time'])
        self.current_index = 0
        self.data_length = len(self.df)
        
    def get_current_market_data(self, strategy_type="straddle"):
        """Get market data for the current timestamp"""
        if self.current_index >= self.data_length:
            return None
            
        current_row = self.df.iloc[self.current_index]
        
        # Calculate spread using high and low prices
        spread = current_row['high'] - current_row['low']
        
        market_data = {
            "timestamp": current_row['time'],
            "bid_price": current_row['low'],
            "ask_price": current_row['high'],
            "current_price": current_row['close'],
            "volume": current_row['Volume'],
            "volume_ma": current_row['Volume MA'],
            "rsi": current_row['RSI'],
            "macd": current_row['MACD'],
            "macd_signal": current_row['Signal'],
            "stoch_k": current_row['%K'],
            "stoch_d": current_row['%D'],
            "upper_band": current_row['Upper Bollinger Band'],
            "lower_band": current_row['Lower Bollinger Band'],
            "spread": spread
        }
        
        # Add strategy-specific calculations
        if strategy_type == "straddle":
            market_data.update({
                "implied_volatility": current_row['RSI'],  # Using RSI as a proxy for volatility
                "delta": (current_row['MACD'] - current_row['Signal']) / 100  # Using MACD difference as a proxy for delta
            })
        
        return market_data
    
    def advance(self):
        """Move to next data point"""
        self.current_index += 1
        return self.current_index < self.data_length
    
    def is_data_available(self):
        """Check if more data is available"""
        return self.current_index < self.data_length

def calculate_price_change(current_price, previous_price):
    """Calculate actual price change between two points"""
    return current_price - previous_price if previous_price else 0
