# Save this as `trading_strategy.py`
import pandas as pd
import numpy as np
import talib
import logging
import os
from config import CONFIG

class TradingStrategy:
    def __init__(self, config):
        self.config = config
        self.position = None
        self.balance = config["initial_balance"]
        self.trade_log = []
        
        os.makedirs(os.path.dirname(config["log_file"]), exist_ok=True)
        logging.basicConfig(
            filename=config["log_file"],
            level=getattr(logging, config["logging"]["level"]),
            format=config["logging"]["format"],
            datefmt=config["logging"]["datefmt"]
        )
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(config["logging"]["format"])
        console_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(console_handler)
    
    def load_data(self):
        if not os.path.exists(self.config["csv_file"]):
            raise FileNotFoundError("CSV file not found.")
        df = pd.read_csv(self.config["csv_file"])
        required_columns = ['open', 'high', 'low', 'close', 'Volume']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        return df

    def calculate_indicators(self, df):
        df['RSI'] = talib.RSI(df['close'], timeperiod=self.config["indicators"]["rsi"]["period"])
        macd, signal, hist = talib.MACD(df['close'], 
                                        fastperiod=self.config["indicators"]["macd"]["fast_period"],
                                        slowperiod=self.config["indicators"]["macd"]["slow_period"],
                                        signalperiod=self.config["indicators"]["macd"]["signal_period"])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        upper, middle, lower = talib.BBANDS(df['close'], 
                                            timeperiod=self.config["indicators"]["bollinger"]["period"], 
                                            nbdevup=self.config["indicators"]["bollinger"]["std_dev"],
                                            nbdevdn=self.config["indicators"]["bollinger"]["std_dev"])
        df['BB_Upper'] = upper
        df['BB_Middle'] = middle
        df['BB_Lower'] = lower
        return df

    def generate_signals(self, df):
        df['Signal'] = 0
        df.loc[(df['RSI'] < 30) & (df['MACD'] > df['MACD_Signal']), 'Signal'] = 1
        df.loc[(df['RSI'] > 70) & (df['MACD'] < df['MACD_Signal']), 'Signal'] = -1
        return df['Signal']

    def execute_trades(self, df, signals):
        total_trades = 0
        successful_trades = 0

        for i, signal in enumerate(signals):
            if signal == 1:  # Buy
                self.position = df['close'][i]
            elif signal == -1 and self.position:  # Sell
                profit = df['close'][i] - self.position
                self.balance += profit
                self.trade_log.append({'buy': self.position, 'sell': df['close'][i], 'profit': profit})
                self.position = None
                total_trades += 1
                if profit > 0:
                    successful_trades += 1
        return total_trades, successful_trades

    def run_strategy(self):
        df = self.load_data()
        df = self.calculate_indicators(df)
        signals = self.generate_signals(df)
        total_trades, successful_trades = self.execute_trades(df, signals)
        return {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "balance": self.balance
        }

if __name__ == "__main__":
    strategy = TradingStrategy(CONFIG)
    print(strategy.run_strategy())
