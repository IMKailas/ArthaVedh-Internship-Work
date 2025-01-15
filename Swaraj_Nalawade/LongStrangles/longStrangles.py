import pandas as pd
import numpy as np
from datetime import datetime
import math
import logging
import config

def load_market_data(csv_file):
    """Load and preprocess the CSV data"""
    try:
        df = pd.read_csv(csv_file)
        df['time'] = pd.to_datetime(df['time'], dayfirst=True)
        
        # Convert relevant columns to numeric
        numeric_columns = ['open', 'high', 'low', 'close', 'VWAP', 'RSI']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate Bollinger Bands if they're NaN
        if 'Upper Bollinger Band' not in df.columns or df['Upper Bollinger Band'].isna().all():
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['Upper Bollinger Band'] = sma + (std * 2)
            df['Lower Bollinger Band'] = sma - (std * 2)
        
        # Calculate synthetic indicators
        df['historical_volatility'] = df['close'].pct_change().rolling(
            window=config.VOLATILITY_WINDOW).std() * np.sqrt(252) * 100
            
        df['synthetic_iv'] = (
            config.VWAP_WEIGHT * (df['close'] - df['VWAP']).abs() / df['VWAP'] * 100 +
            config.RSI_WEIGHT * df['RSI'] / 100 * df['historical_volatility']
        )
        
        # Calculate synthetic delta using normalized price
        bb_range = df['Upper Bollinger Band'] - df['Lower Bollinger Band']
        price_from_lower = df['close'] - df['Lower Bollinger Band']
        df['synthetic_delta'] = price_from_lower.div(bb_range).fillna(0.5)
        df['synthetic_delta'] = (df['synthetic_delta'] - 0.5) * 2
        
        # Forward fill NaN values
        df['synthetic_delta'] = df['synthetic_delta'].ffill()
        df['synthetic_iv'] = df['synthetic_iv'].ffill()
        
        print("\nData Overview:")
        print(f"Total rows: {len(df)}")
        print(f"Date range: {df['time'].min().strftime('%Y-%m-%d')} to {df['time'].max().strftime('%Y-%m-%d')}")
        print("\nSample of loaded data:")
        print(df.head(1).to_string())
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        raise

class LongStranglesStrategy:
    def __init__(self, data_path):
        self.logger = self._setup_logging()
        self.data = load_market_data(data_path)
        self.balance = config.INITIAL_BALANCE
        self.positions = []
        self.trade_history = []
        
    def _setup_logging(self):
        """Configure logging settings"""
        logger = logging.getLogger('LongStrangles')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_filename = f"long_strangles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _calculate_position_size(self, current_price):
        """Calculate position size based on risk parameters"""
        risk_amount = self.balance * config.RISK_PER_TRADE
        max_contracts = min(
            math.floor(risk_amount / (current_price * 100)),
            config.MAX_POSITION_SIZE
        )
        return max(1, max_contracts)
    
    def _check_entry_conditions(self, row):
        """Check if entry conditions are met"""
        iv_condition = config.MIN_IMPLIED_VOLATILITY <= row['synthetic_iv'] <= config.MAX_IMPLIED_VOLATILITY
        delta_call = abs(row['synthetic_delta'] - config.CALL_DELTA_TARGET) <= config.DELTA_TOLERANCE
        delta_put = abs(row['synthetic_delta'] - config.PUT_DELTA_TARGET) <= config.DELTA_TOLERANCE
        
        return iv_condition and (delta_call or delta_put)
    
    def _check_exit_conditions(self, position, current_row):
        """Check if exit conditions are met for a position"""
        days_held = (current_row['time'] - position['entry_time']).days
        
        # Calculate P&L
        call_pnl = (current_row['synthetic_delta'] - position['call_entry_delta']) * 100
        put_pnl = (current_row['synthetic_delta'] - position['put_entry_delta']) * 100
        total_pnl = (call_pnl + put_pnl) * position['contracts']
        
        # Exit conditions
        profit_target_hit = total_pnl >= position['max_profit'] * config.PROFIT_TARGET_PERCENT / 100
        stop_loss_hit = total_pnl <= -position['premium_paid']
        max_hold_reached = days_held >= config.MAX_HOLD_DAYS
        iv_too_low = current_row['synthetic_iv'] < config.IV_EXIT_THRESHOLD
        
        return {
            'should_exit': profit_target_hit or stop_loss_hit or max_hold_reached or iv_too_low,
            'pnl': total_pnl,
            'exit_reason': 'Profit Target' if profit_target_hit else
                          'Stop Loss' if stop_loss_hit else
                          'Max Hold Time' if max_hold_reached else
                          'Low IV' if iv_too_low else None
        }
    
    def run_strategy(self):
        """Execute the long strangles strategy"""
        self.logger.info("Starting Long Strangles Strategy")
        self.logger.info(f"Initial Balance: ${self.balance:,.2f}")
        
        start_index = max(20, config.MIN_LOOKBACK)  # Start after indicators have enough data
        
        for index, row in self.data.iloc[start_index:].iterrows():
            # Update existing positions
            for position in self.positions[:]:
                exit_check = self._check_exit_conditions(position, row)
                
                if exit_check['should_exit']:
                    self.balance += exit_check['pnl']
                    position['exit_time'] = row['time']
                    position['exit_price'] = row['close']
                    position['pnl'] = exit_check['pnl']
                    position['exit_reason'] = exit_check['exit_reason']
                    
                    self.trade_history.append(position)
                    self.positions.remove(position)
                    
                    self.logger.info(f"\nClosed strangle position:")
                    self.logger.info(f"Entry: {position['entry_time'].strftime('%Y-%m-%d')} - Exit: {position['exit_time'].strftime('%Y-%m-%d')}")
                    self.logger.info(f"P&L: ${exit_check['pnl']:,.2f}")
                    self.logger.info(f"Exit Reason: {exit_check['exit_reason']}")
                    self.logger.info(f"Current Balance: ${self.balance:,.2f}")
            
            # Check for new entry if we have capacity
            if len(self.positions) < config.MAX_POSITION_SIZE and self._check_entry_conditions(row):
                if not self.positions or (row['time'] - self.positions[-1]['entry_time']).days >= config.MIN_DAYS_BETWEEN_TRADES:
                    contracts = self._calculate_position_size(row['close'])
                    premium = row['close'] * 0.05  # Approximate premium as 5% of underlying price
                    
                    new_position = {
                        'entry_time': row['time'],
                        'entry_price': row['close'],
                        'contracts': contracts,
                        'call_entry_delta': row['synthetic_delta'],
                        'put_entry_delta': -row['synthetic_delta'],
                        'entry_iv': row['synthetic_iv'],
                        'premium_paid': premium * contracts * 100,
                        'max_profit': premium * contracts * 100 * 2
                    }
                    
                    self.positions.append(new_position)
                    self.logger.info(f"\nOpened new strangle position:")
                    self.logger.info(f"Time: {row['time'].strftime('%Y-%m-%d')}")
                    self.logger.info(f"Price: ${row['close']:,.2f}")
                    self.logger.info(f"Contracts: {contracts}")
                    self.logger.info(f"Synthetic IV: {row['synthetic_iv']:.1f}%")
                    self.logger.info(f"Synthetic Delta: {row['synthetic_delta']:.2f}")
        
        # Save trade history and generate summary
        if self.trade_history:
            history_df = pd.DataFrame(self.trade_history)
            history_df.to_csv(f"strangle_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
            
            total_trades = len(history_df)
            profitable_trades = len(history_df[history_df['pnl'] > 0])
            total_pnl = history_df['pnl'].sum()
            
            self.logger.info("\nStrategy Summary:")
            self.logger.info(f"Total Trades: {total_trades}")
            self.logger.info(f"Profitable Trades: {profitable_trades}")
            self.logger.info(f"Win Rate: {(profitable_trades/total_trades*100):.1f}%")
            self.logger.info(f"Initial Balance: ${config.INITIAL_BALANCE:,.2f}")
            self.logger.info(f"Final Balance: ${self.balance:,.2f}")
            self.logger.info(f"Total P&L: ${total_pnl:,.2f}")
            self.logger.info(f"Return: {(total_pnl/config.INITIAL_BALANCE*100):.1f}%")
        
        return self.balance, self.trade_history

if __name__ == "__main__":
    strategy = LongStranglesStrategy(config.DATA_PATH)
    final_balance, trades = strategy.run_strategy()
