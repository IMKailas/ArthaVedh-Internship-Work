import pandas as pd
import numpy as np
import talib
import logging
import os
from datetime import datetime
from config import CONFIG

class TradingStrategy:
    def __init__(self, config):
        self.config = config
        self.position = None
        self.balance = config["initial_balance"]
        self.trade_log = []
        
        # Ensure log directory exists
        log_dir = os.path.dirname(config["log_file"])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup logging
        logging.basicConfig(
            filename=config["log_file"],
            level=getattr(logging, config["logging"]["level"]),
            format=config["logging"]["format"],
            datefmt=config["logging"]["datefmt"]
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(config["logging"]["format"])
        console_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(console_handler)
    
    def load_data(self):
        """Load and validate CSV data"""
        if not os.path.exists(self.config["csv_file"]):
            raise FileNotFoundError(
                f"CSV file not found at {self.config['csv_file']}. "
                f"Please ensure your data file is placed in the 'data' directory "
                f"and named correctly."
            )
        
        try:
            df = pd.read_csv(self.config["csv_file"])
            required_columns = ['open', 'high', 'low', 'close', 'Volume']
            
            # Check for required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(
                    f"Missing required columns in CSV: {missing_columns}. "
                    f"Required columns are: {required_columns}"
                )
            
            return df
            
        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty.")
        except pd.errors.ParserError:
            raise ValueError("Error parsing CSV file. Please ensure it's properly formatted.")

    def calculate_indicators(self, df):
        """Calculate technical indicators using TALib"""
        try:
            # Convert price columns to float if they're not already
            for col in ['open', 'high', 'low', 'close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Check for NaN values after conversion
            if df[['open', 'high', 'low', 'close', 'Volume']].isna().any().any():
                logging.warning("Some price/volume data was converted to NaN. Please check your data.")
            
            # RSI
            df['RSI'] = talib.RSI(df['close'], 
                                timeperiod=self.config["indicators"]["rsi"]["period"])
            
            # MACD
            macd, signal, hist = talib.MACD(
                df['close'],
                fastperiod=self.config["indicators"]["macd"]["fast_period"],
                slowperiod=self.config["indicators"]["macd"]["slow_period"],
                signalperiod=self.config["indicators"]["macd"]["signal_period"]
            )
            df['MACD'] = macd
            df['MACD_Signal'] = signal
            df['MACD_Hist'] = hist
            
            # Bollinger Bands
            upper, middle, lower = talib.BBANDS(
                df['close'],
                timeperiod=self.config["indicators"]["bollinger"]["period"],
                nbdevup=self.config["indicators"]["bollinger"]["std_dev"],
                nbdevdn=self.config["indicators"]["bollinger"]["std_dev"]
            )
            df['BB_Upper'] = upper
            df['BB_Middle'] = middle
            df['BB_Lower'] = lower
            
            # Stochastic
            slowk, slowd = talib.STOCH(
                df['high'],
                df['low'],
                df['close'],
                fastk_period=self.config["indicators"]["stochastic"]["k_period"],
                slowk_period=self.config["indicators"]["stochastic"]["slowing"],
                slowk_matype=0,
                slowd_period=self.config["indicators"]["stochastic"]["d_period"],
                slowd_matype=0
            )
            df['STOCH_K'] = slowk
            df['STOCH_D'] = slowd
            
            # Volume MA
            df['Volume_MA'] = talib.SMA(df['Volume'], 
                                      timeperiod=self.config["indicators"]["vwap"]["period"])
            
            return df
            
        except Exception as e:
            logging.error(f"Error calculating indicators: {str(e)}")
            raise

    # ... [rest of the class implementation remains the same] ...

    def run_strategy(self):
        """Run the complete trading strategy"""
        try:
            # Load and prepare data
            logging.info("Loading market data...")
            df = self.load_data()
            
            logging.info("Calculating technical indicators...")
            df = self.calculate_indicators(df)
            
            logging.info("Generating trading signals...")
            signals = self.generate_signals(df)
            
            logging.info("Executing trades...")
            total_trades, successful_trades = self.execute_trades(df, signals)
            
            # Calculate final statistics
            win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
            profit_loss = self.balance - self.config["initial_balance"]
            
            # Log final results
            logging.info(f"=== Strategy Results ===")
            logging.info(f"Total Trades: {total_trades}")
            logging.info(f"Successful Trades: {successful_trades}")
            logging.info(f"Win Rate: {win_rate:.2f}%")
            logging.info(f"Final Balance: {self.balance:.2f}")
            logging.info(f"Total P&L: {profit_loss:.2f}")
            
            return {
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'win_rate': win_rate,
                'final_balance': self.balance,
                'profit_loss': profit_loss,
                'trade_log': self.trade_log
            }
            
        except Exception as e:
            logging.error(f"Strategy execution failed: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        strategy = TradingStrategy(CONFIG)
        results = strategy.run_strategy()
        
        # Print results to console
        print("\n=== Trading Strategy Results ===")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Successful Trades: {results['successful_trades']}")
        print(f"Win Rate: {results['win_rate']:.2f}%")
        print(f"Final Balance: {results['final_balance']:.2f}")
        print(f"Total P&L: {results['profit_loss']:.2f}")
        
    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
        print("\nTo fix this:")
        print("1. Create a 'data' directory in your project folder")
        print("2. Place your CSV file in the 'data' directory")
        print("3. Ensure the CSV file is named 'NSE_NIFTY_1_Intraday.csv'")
        print("\nOr update the csv_file path in config.py to match your file location")
    except Exception as e:
        print(f"\nError: {str(e)}")