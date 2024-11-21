import pandas as pd
import numpy as np
import logging
from datetime import datetime

def setup_logging():
    """Configure logging with custom format showing trade timestamps"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        filename=f"rsi_trading_log_{datetime.now().strftime('%Y%m%d')}.log"
    )

def identify_rsi_signals(df):
    """
    Enhanced signal identification with more flexible conditions
    """
    # Debugging print statements
    print("Generating Signals...")
    
    # Basic RSI Conditions
    rsi_oversold = df['RSI'] <= 30
    rsi_overbought = df['RSI'] >= 70
    
    # MACD Confirmation
    macd_bullish = df['MACD'] > df['Signal']
    macd_bearish = df['MACD'] < df['Signal']
    
    # Stochastic Oscillator Confirmation
    stoch_bullish = (df['%K'] > df['%D']) & (df['%K'] <= 20)
    stoch_bearish = (df['%K'] < df['%D']) & (df['%K'] >= 80)
    
    # Bollinger Band Context
    bollinger_lower_penetration = df['close'] <= df['Lower Bollinger Band']
    bollinger_upper_penetration = df['close'] >= df['Upper Bollinger Band']
    
    # Additional Volume Confirmation
    volume_surge = df['Volume'] > df['Volume MA'] * 1.2
    
    # Bullish Signal Combination
    bullish_signal = (
        (rsi_oversold | (stoch_bullish & macd_bullish)) &
        (bollinger_lower_penetration | volume_surge)
    )
    
    # Bearish Signal Combination
    bearish_signal = (
        (rsi_overbought | (stoch_bearish & macd_bearish)) &
        (bollinger_upper_penetration | volume_surge)
    )
    
    # Debugging: Print signal counts
    print(f"Bullish Signals: {bullish_signal.sum()}")
    print(f"Bearish Signals: {bearish_signal.sum()}")
    
    return bullish_signal, bearish_signal

def log_trade(trade_type, action, price, time, reason=None, profit=None, balance=None):
    """Enhanced trade logging with detailed information"""
    if action == "ENTRY":
        log_msg = (
            f"[{time}] {trade_type} ENTRY\n"
            f"Price: {price:.2f}\n"
            f"Current Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    else:  # EXIT
        log_msg = (
            f"[{time}] {trade_type} EXIT\n"
            f"Price: {price:.2f}\n"
            f"Reason: {reason}\n"
            f"Profit/Loss: {profit:.2f}\n"
            f"New Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    logging.info(log_msg)

def print_trading_summary(trades_df, initial_balance, final_balance):
    """Comprehensive trading summary with detailed statistics"""
    if len(trades_df) == 0:
        print("\nNo trades were executed during this period.")
        return

    # Calculate basic statistics
    total_trades = len(trades_df)
    profitable_trades = len(trades_df[trades_df['profit'] > 0])
    loss_trades = len(trades_df[trades_df['profit'] <= 0])
    win_rate = (profitable_trades / total_trades) * 100
    total_profit = trades_df['profit'].sum()
    avg_profit = trades_df['profit'].mean()
    max_profit = trades_df['profit'].max()
    max_loss = trades_df['profit'].min()
    
    # Calculate trade types distribution
    long_trades = len(trades_df[trades_df['type'] == 'LONG'])
    short_trades = len(trades_df[trades_df['type'] == 'SHORT'])
    
    # Calculate exit reason distribution
    exit_reasons = trades_df['reason'].value_counts()
    
    # Print summary with formatting
    print("\n" + "="*60)
    print(f"{'RSI TRADING SUMMARY':^60}")
    print("="*60)
    
    # Performance Metrics
    print("\nPERFORMANCE METRICS")
    print("-"*60)
    print(f"Initial Balance:      ${initial_balance:,.2f}")
    print(f"Final Balance:        ${final_balance:,.2f}")
    print(f"Total Profit/Loss:    ${total_profit:,.2f}")
    print(f"Return on Investment: {((final_balance - initial_balance) / initial_balance * 100):,.2f}%")
    
    # Trade Statistics
    print("\nTRADE STATISTICS")
    print("-"*60)
    print(f"Total Trades:         {total_trades}")
    print(f"Profitable Trades:    {profitable_trades}")
    print(f"Loss-Making Trades:   {loss_trades}")
    print(f"Win Rate:            {win_rate:.2f}%")
    print(f"Average Profit:      ${avg_profit:.2f}")
    print(f"Maximum Profit:      ${max_profit:.2f}")
    print(f"Maximum Loss:        ${max_loss:.2f}")
    
    # Exit Reason Analysis
    print("\nEXIT REASON ANALYSIS")
    print("-"*60)
    for reason, count in exit_reasons.items():
        print(f"{reason:.<20} {count:>3} trades ({(count/total_trades*100):>6.1f}%)")
    
    print("\n" + "="*60)

def run_rsi_strategy(data_path, initial_balance=10000, stop_loss_pct=1.5, target_profit_pct=3.0):
    # Load and prepare data
    df = pd.read_csv(data_path, parse_dates=['time'])
    df = df.sort_values('time')
    
    # Compute some initial stats to help with debugging
    print("Data Overview:")
    print(f"Total Data Points: {len(df)}")
    print(f"Date Range: {df['time'].min()} to {df['time'].max()}")
    print(f"RSI Range: {df['RSI'].min()} to {df['RSI'].max()}")
    
    # Setup logging
    setup_logging()
    
    # Trading variables
    balance = initial_balance
    position = None
    entry_price = None
    trade_history = []
    
    # Get signals
    bullish_signals, bearish_signals = identify_rsi_signals(df)
    
    # Main trading loop
    for i in range(50, len(df)):
        current_time = df['time'].iloc[i]
        current_price = df['close'].iloc[i]
        
        # Position entry logic
        if position is None:
            if bullish_signals.iloc[i]:
                position = "LONG"
                entry_price = current_price
                log_trade("LONG", "ENTRY", current_price, current_time, balance=balance)
                
            elif bearish_signals.iloc[i]:
                position = "SHORT"
                entry_price = current_price
                log_trade("SHORT", "ENTRY", current_price, current_time, balance=balance)
        
        # Position exit logic
        elif position == "LONG":
            profit = current_price - entry_price
            stop_loss = entry_price * (1 - stop_loss_pct/100)
            target = entry_price * (1 + target_profit_pct/100)
            
            if current_price <= stop_loss or current_price >= target or bearish_signals.iloc[i]:
                balance += profit
                trade_history.append({
                    "type": "LONG", 
                    "profit": profit, 
                    "reason": "Stop Loss" if current_price <= stop_loss else 
                              "Target Reached" if current_price >= target else 
                              "Signal Reversal"
                })
                position = None
        
        elif position == "SHORT":
            profit = entry_price - current_price
            stop_loss = entry_price * (1 + stop_loss_pct/100)
            target = entry_price * (1 - target_profit_pct/100)
            
            if current_price >= stop_loss or current_price <= target or bullish_signals.iloc[i]:
                balance += profit
                trade_history.append({
                    "type": "SHORT", 
                    "profit": profit, 
                    "reason": "Stop Loss" if current_price >= stop_loss else 
                              "Target Reached" if current_price <= target else 
                              "Signal Reversal"
                })
                position = None
    
    # Create trades DataFrame and print summary
    trades_df = pd.DataFrame(trade_history)
    
    # Print diagnostics if no trades
    if len(trades_df) == 0:
        print("\nDiagnostic Information:")
        print("Potential reasons for no trades:")
        print("1. Signal generation conditions too strict")
        print("2. Insufficient volatility in the data")
        print("3. RSI not showing clear overbought/oversold conditions")
    
    print("\nTrading Summary:")
    print(f"Total Trades: {len(trades_df)}")
    print(f"Initial Balance: {initial_balance}")
    print(f"Final Balance: {balance}")
    
    return balance, trades_df

if __name__ == "__main__":
    # Path to your CSV file
    DATA_PATH = "NSE_NIFTY, 1D.csv"
    final_balance, trades = run_rsi_strategy(
        DATA_PATH,
        initial_balance=10000,
        stop_loss_pct=1.5,
        target_profit_pct=3.0
    )
